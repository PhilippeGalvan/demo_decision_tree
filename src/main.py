"""
To avoid storing data in memory for strategies, a yield strategy can be applied
This logic can also be applied to the file reader (instead of storing an in memory image of the tree, we can crawl linarly through it each time instead of accessing the dict)
Another trick would be to store the tree in a db and benefit from indexed access :p
"""

from collections import defaultdict
from dataclasses import dataclass
from logging import DEBUG, basicConfig, getLogger
from pathlib import Path
from typing import Any, Self

from src.feature_flags import IGNORE_ALWAYS_FALSE_STRATEGIES

basicConfig(level=DEBUG)
logger = getLogger(__name__)


class AlwaysFalseStrategyError(Exception):
    pass


class NodelessTreeError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Condition:
    feature: str
    value: str
    is_equal: bool

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Create a Condition from a string.

        >>> Condition.from_string("device_type=pc")
        Condition(feature='device_type', value='pc', is_equal=True)
        """
        equality_per_operator = {
            "=": True,
            "!=": False,
        }

        operator = "="
        if "!=" in string:
            operator = "!="

        feature, value = string.split(operator)
        return cls(feature, value, equality_per_operator[operator])

    def to_strategy_format(self) -> str:
        """
        Convert a condition to a strategy format.

        >>> Condition("device_type", "pc", is_equal=True).to_strategy_format()
        'device_type=pc'
        """
        operator = "="
        if not self.is_equal:
            operator = "!="

        return f"{self.feature}{operator}{self.value}"


@dataclass(frozen=True, slots=True)
class Leaf:
    value: float

    @classmethod
    def from_standardized_string(cls, definition: str) -> Self:
        """
        Create a Leaf from a standardized string.

        >>> Leaf.from_standardized_string("0:leaf=0.0")
        Leaf(value=0.0)
        """
        _, value = definition.split(":leaf=")
        return cls(float(value))

    def __post_init__(self):
        if not 0 <= self.value <= 1:
            raise ValueError(f"Invalid leaf value: {self.value}, must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Node:
    eligible_conditions: tuple[Condition, ...]
    yes: str
    no: str

    @classmethod
    def from_standardized_string(cls, definition: str) -> Self:
        """
        Create a Node from a standardized string.

        >>> Node.from_standardized_string("0:[device_type=pc] yes=1,no=2")
        Node(eligible_conditions=(Condition(feature='device_type', value='pc', is_equal=True),), yes='1', no='2')
        """
        raw_condition, branches = definition.split(":[", 1)[1].split("] ", 1)

        yes, no = branches.split(",")
        yes = yes.removeprefix("yes=").strip()
        no = no.removeprefix("no=").strip()

        raw_conditions = [raw_condition]
        if "||or||" in definition:
            raw_conditions = raw_condition.split("||or||")

        conditions = tuple(
            Condition.from_string(raw_condition) for raw_condition in raw_conditions
        )
        return cls(conditions, yes, no)


@dataclass(frozen=True, slots=True)
class Strategy:
    conditions: tuple[Condition, ...]
    value: Leaf

    def to_human_readable_format(self) -> str:
        """
        Convert a strategy to a human readable format.

        >>> Strategy(
        ...     (Condition("device_type", "pc", is_equal=True),),
        ...     Leaf(1.0),
        ... ).to_human_readable_format()
        'device_type=pc : 1.0'
        >>> Strategy(
        ...     (Condition("device_type", "pc", is_equal=True), Condition("os", "linux", is_equal=True)),
        ...     Leaf(0.1),
        ... ).to_human_readable_format()
        'device_type=pc & os=linux : 0.1'
        """
        formated_condition = " & ".join(
            condition.to_strategy_format() for condition in self.conditions
        )
        return f"{formated_condition} : {self.value.value}"

    def __post_init__(self):
        if IGNORE_ALWAYS_FALSE_STRATEGIES:
            self._forbid_always_false_strategies()

    def _forbid_always_false_strategies(self) -> None:
        # This grouping by feature is O(n2) reduces the number of comparisons only to the features having multiple conditions
        conditions_grouped_by_feature: dict[str, list[Condition]] = defaultdict(list)
        for condition in self.conditions:
            conditions_grouped_by_feature[condition.feature].append(condition)

        for feature_conditions in conditions_grouped_by_feature.values():
            if len(feature_conditions) == 1:
                continue

            for index, condition_pointer in enumerate(feature_conditions):
                for condition_evaluated in feature_conditions[index + 1 :]:
                    has_same_feature_equality_on_different_values = (
                        condition_pointer.feature == condition_evaluated.feature
                        and condition_pointer.value != condition_evaluated.value
                        and (
                            condition_pointer.is_equal
                            is condition_evaluated.is_equal
                            is True
                        )
                    )

                    has_same_feature_inequality_on_same_value = (
                        condition_pointer.feature == condition_evaluated.feature
                        and condition_pointer.value == condition_evaluated.value
                        and condition_pointer.is_equal
                        is not condition_evaluated.is_equal
                    )

                    if (
                        has_same_feature_equality_on_different_values
                        or has_same_feature_inequality_on_same_value
                    ):
                        raise AlwaysFalseStrategyError(
                            f"Always false strategy: {self} for {condition_pointer} and {condition_evaluated}"
                        )


Tree = dict[str, Leaf | Node]
BinaryTree = dict[Condition, Any]


def _parse_tree_row(row: str) -> Leaf | Node:
    if ":leaf" in row:
        return Leaf.from_standardized_string(row)

    return Node.from_standardized_string(row)


def parse_tree(tree: str) -> BinaryTree:
    raw_tree = [line.strip() for line in tree.splitlines()]

    parsed_tree: dict[str, Leaf | Node] = {}
    for line_index, line in enumerate(raw_tree):
        if not line:
            logger.debug(f"Skipping empty line: {line_index}")
            continue

        id = line.split(":", 1)[0]
        if id in parsed_tree:
            raise ValueError(f"Unexpected duplicate id: {id}")

        parsed_tree[id] = _parse_tree_row(line)

    binary_tree = _tree_to_binary_tree(parsed_tree)
    if isinstance(binary_tree, Leaf):
        raise NodelessTreeError("Expected a tree with at least one node")

    return binary_tree


def _tree_to_binary_tree(
    tree: Tree, current_node: Node | Leaf | None = None
) -> BinaryTree | Leaf:
    """
    Convert a tree to a binary tree
    """
    if current_node is None:
        current_node = next(iter(tree.values()))

    if isinstance(current_node, Leaf):
        return current_node

    if len(current_node.eligible_conditions) == 2:
        # Morgan's law: not (A and B) <=> (not A) or (not B)
        return {
            current_node.eligible_conditions[0]: {
                True: _tree_to_binary_tree(tree, tree[current_node.yes]),
                False: {
                    current_node.eligible_conditions[1]: {
                        True: None,  # Skip redundant strategy
                        False: _tree_to_binary_tree(tree, tree[current_node.no]),
                    },
                },
            },
            current_node.eligible_conditions[1]: {
                True: _tree_to_binary_tree(tree, tree[current_node.yes]),
                False: None,  # Skip redundant strategy
            },
        }

    return {
        current_node.eligible_conditions[0]: {
            True: _tree_to_binary_tree(tree, tree[current_node.yes]),
            False: _tree_to_binary_tree(tree, tree[current_node.no]),
        }
    }


def read_strategies_from_tree(tree: BinaryTree) -> set[Strategy]:
    strategies = set()

    def crawl(subtree: BinaryTree | Leaf | None, conditions: tuple[Condition, ...]):
        if isinstance(subtree, Leaf):
            try:
                strategies.add(Strategy(conditions, subtree))
            except AlwaysFalseStrategyError as e:
                logger.debug(e)
            finally:
                return

        if subtree is None:
            # Skip redundant strategy
            return

        for condition, next_subtree in subtree.items():
            negative_condition = Condition(
                condition.feature, condition.value, not condition.is_equal
            )

            crawl(next_subtree[True], conditions + (condition,))
            crawl(next_subtree[False], conditions + (negative_condition,))

    crawl(tree, tuple())
    return strategies


def main(tree_file_path: Path, strategies_file_path: Path):
    with open(tree_file_path) as f:
        tree = f.read()

    binary_tree = parse_tree(tree)
    strategies = read_strategies_from_tree(binary_tree)

    with open(strategies_file_path, "w") as f:
        # This is for the sake of output consistency at the expense of some memory
        serialized_strategies = sorted(
            strategy.to_human_readable_format() for strategy in strategies
        )
        for strategy in serialized_strategies:
            f.write(strategy)
            f.write("\n")

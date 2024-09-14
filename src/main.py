"""
To avoid storing data in memory for strategies, a yield strategy can be applied
This logic can also be applied to the file reader (instead of storing an in memory image of the tree, we can crawl linarly through it each time instead of accessing the dict)
Another trick would be to store the tree in a db and benefit from indexed access :p
"""

from logging import DEBUG, basicConfig, getLogger
from pathlib import Path

from .exceptions import AlwaysFalseStrategyError, NodelessTreeError
from .local_types import BinaryTree, Tree
from .models import Condition, Leaf, Node, Strategy

basicConfig(level=DEBUG)
logger = getLogger(__name__)


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


def main(tree_file_path: Path, strategies_file_path: Path) -> None:
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

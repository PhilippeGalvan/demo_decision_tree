from dataclasses import dataclass
from logging import DEBUG, basicConfig, getLogger
from typing import Self

basicConfig(level=DEBUG)
logger = getLogger(__name__)


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
        Condition(feature='device_type', value='pc')
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


@dataclass(frozen=True, slots=True)
class AndCondition:
    conditions: list[Condition]

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Create an AndCondition from a string.

        >>> AndCondition.from_string("device_type=pc||and||os=linux")
        AndCondition(conditions=[Condition(feature='device_type', value='pc', is_equal=True), Condition(feature='os', value='linux', is_equal=True)])

        >>> AndCondition.from_string("device_type=pc")
        AndCondition(conditions=[Condition(feature='device_type', value='pc', is_equal=True)])

        >>> AndCondition.from_string("device_type=pc||or||os=linux")
        AndCondition(conditions=[Condition(feature='device_type', value='pc', is_equal=False), Condition(feature='os', value='linux', is_equal=False)])
        """
        or_count = string.count("||or||")
        and_count = string.count("||and||")

        if or_count + and_count > 1:
            raise ValueError("Only pairs of conditions are supported")

        conditions = [string]
        if "||or||" in string:
            # De Morgan's Law: (A || B) == !(!A && !B)
            and_converted_string = string.replace("=", "!=")
            conditions = and_converted_string.split("||or||")

        if "||and||" in string:
            conditions = string.split("||and||")

        return cls([Condition.from_string(condition) for condition in conditions])


@dataclass(frozen=True, slots=True)
class Leaf:
    value: float

    @classmethod
    def from_standardized_string(cls, string: str) -> Self:
        """
        Create a Leaf from a standardized string.

        >>> Leaf.from_standardized_string("0:leaf=0.0")
        Leaf(value=0.0)
        """
        _, value = string.split(":leaf=")
        return cls(float(value))


@dataclass(frozen=True, slots=True)
class Node:
    condition: AndCondition
    yes: Leaf | Self
    no: Leaf | Self

    @classmethod
    def from_standardized_string(cls, string: str) -> Self:
        """
        Create a Node from a standardized string.

        >>> Node.from_standardized_string("0:[device_type=pc] yes=1,no=2")
        Node(condition='device_type=pc', yes='1', no='2')
        """
        _, raw_node = string.split(":")
        raw_condition, branches = raw_node.split(" ")

        condition = AndCondition.from_string(
            raw_condition.removeprefix("[").removesuffix("]")
        )

        yes, no = branches.split(",")
        yes = yes.removeprefix("yes=").strip()
        no = no.removeprefix("no=").strip()

        return cls(condition, yes, no)


Tree = dict[str, Leaf | Node]


def tree_parser(tree: str) -> Tree:
    raw_tree = [line.strip() for line in tree.splitlines("\n")]

    parsed_tree = {}
    for line_index, line in enumerate(raw_tree):
        if not line:
            logger.debug(f"Skipping empty line: {line_index}")
            continue

        id = line[0]
        if id in parsed_tree:
            raise ValueError(f"Unexpected duplicate id: {id}")

        if ":leaf" in line:
            leaf = Leaf.from_standardized_string(line)
            parsed_tree[id] = leaf
            continue

        if ":[" in line:
            node = Node.from_standardized_string(line)
            parsed_tree[id] = node
            continue

        raise ValueError(f"Cant parse line: {line}")

    return parsed_tree

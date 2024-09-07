from dataclasses import dataclass
from logging import DEBUG, basicConfig, getLogger
from typing import Self

basicConfig(level=DEBUG)
logger = getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Condition:
    feature: str
    value: str

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Create a Condition from a string.

        >>> Condition.from_string("device_type=pc")
        Condition(feature='device_type', value='pc')
        """
        feature, value = string.split("=")
        return cls(feature, value)


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
    condition: str
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

        condition = Condition.from_string(
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

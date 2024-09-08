from dataclasses import dataclass

from src.main import Condition, Leaf, Node, Tree


@dataclass(frozen=True, slots=True)
class Strategy:
    conditions: tuple[Condition]
    value: Leaf


def test_should_read_strategy_from_single_leaf_tree():
    one_leaf_tree = {"0": Leaf(1.0)}

    strategies = compute_strategies_from_tree(one_leaf_tree)

    assert strategies == {Strategy(tuple(), Leaf(1.0))}


def compute_strategies_from_tree(
    tree: Tree, current_node: Node | None = None, pre_conditions: set[Condition] = set()
) -> set[Strategy]:
    """
    strategies can be computed by crawling through tree nodes up to leaves
    """
    if current_node is None:
        current_node = next(iter(tree.values()))

    if isinstance(current_node, Leaf):
        return {Strategy(tuple(pre_conditions), current_node)}

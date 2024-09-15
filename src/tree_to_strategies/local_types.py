from typing import Any

from src.tree_to_strategies.models import Condition, Leaf, Node

Tree = dict[str, Leaf | Node]
BinaryTree = dict[Condition, Any]

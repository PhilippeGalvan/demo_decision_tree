from typing import Any

from .models import Condition, Leaf, Node

Tree = dict[str, Leaf | Node]
BinaryTree = dict[Condition, Any]

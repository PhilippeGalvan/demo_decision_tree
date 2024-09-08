from contextlib import nullcontext as does_not_raise

import pytest

from src.main import Condition, Leaf, Node, tree_parser


def test_should_read_single_leaf_tree():
    one_leaf_tree = "0:leaf=0.0"
    assert tree_parser(one_leaf_tree) == {"0": Leaf(0.0)}


def test_should_read_two_leaf_tree():
    two_leaf_tree = """0:leaf=0.0
        1:leaf=1.0
    """
    assert tree_parser(two_leaf_tree) == {
        "0": Leaf(0.0),
        "1": Leaf(1.0),
    }


def test_should_read_single_node_tree():
    one_node_tree = """
        0:[device_type=pc] yes=1,no=2
        1:leaf=0.0
        2:leaf=0.0
    """
    assert tree_parser(one_node_tree) == {
        "0": Node({Condition("device_type", "pc", is_equal=True)}, "1", "2"),
        "1": Leaf(0.0),
        "2": Leaf(0.0),
    }


def test_should_handle_inequalities():
    inequality_tree = """
        0:[device_type!=pc] yes=1,no=2
        1:leaf=0.0
        2:leaf=0.0
    """
    assert tree_parser(inequality_tree) == {
        "0": Node({Condition("device_type", "pc", is_equal=False)}, "1", "2"),
        "1": Leaf(0.0),
        "2": Leaf(0.0),
    }


def test_should_read_nested_node_tree():
    nested_node_tree = """
        0:[device_type=pc] yes=1,no=2
        1:[device_type=mobile] yes=3,no=4
        2:leaf=0.0
        3:leaf=1.0
        4:leaf=0.5
    """
    assert tree_parser(nested_node_tree) == {
        "0": Node({Condition("device_type", "pc", is_equal=True)}, "1", "2"),
        "1": Node({Condition("device_type", "mobile", is_equal=True)}, "3", "4"),
        "2": Leaf(0.0),
        "3": Leaf(1.0),
        "4": Leaf(0.5),
    }


def test_should_log_empty_lines(caplog):
    caplog.set_level(10)

    empty_line_tree = """
        1:leaf=0.0

    """
    tree_parser(empty_line_tree)
    assert "Skipping empty line: 0" in caplog.text
    assert "Skipping empty line: 2" in caplog.text


def test_should_skip_empty_lines():
    empty_line_tree = """

        1:leaf=0.0

    """
    assert tree_parser(empty_line_tree) == {"1": Leaf(0.0)}


def test_should_parse_or_condition_as_branching_conditions():
    tree = """
        0:[device_type=pc||or||os=linux] yes=1,no=2
        1:leaf=1.0
        2:leaf=0.5
    """
    assert tree_parser(tree) == {
        "0": Node(
            {
                Condition("device_type", "pc", is_equal=True),
                Condition("os", "linux", is_equal=True),
            },
            "1",
            "2",
        ),
        "1": Leaf(1.0),
        "2": Leaf(0.5),
    }


@pytest.mark.parametrize(
    [
        "threshold_impossible_leaf_value",
        "expected_behavior",
    ],
    [
        pytest.param("-0.000000000001", pytest.raises(ValueError), id="lower than 0"),
        pytest.param("0.0", does_not_raise(), id="equal to 0"),
        pytest.param("1.0", does_not_raise(), id="equal to 1"),
        pytest.param("1.000000000001", pytest.raises(ValueError), id="greater than 1"),
    ],
)
def test_should_fail_for_leaves_in_impossible_range(
    threshold_impossible_leaf_value: str,
    expected_behavior,
):
    impossible_range_tree = f"""
        0:leaf={threshold_impossible_leaf_value}
    """
    with expected_behavior:
        tree_parser(impossible_range_tree)

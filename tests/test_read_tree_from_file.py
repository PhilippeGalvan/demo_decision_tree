from contextlib import nullcontext as does_not_raise

import pytest

from src.main import Condition, Leaf, NodelessTreeError, parse_tree


def test_should_fail_for_single_leaf_tree():
    """
    We consider that a single leaf tree is a special case where the value should always be 1.0.
    This could be handled specifically if accepted.
    """
    one_leaf_tree = "0:leaf=0.0"
    with pytest.raises(NodelessTreeError):
        assert parse_tree(one_leaf_tree)


def test_should_read_single_node_tree():
    one_node_tree = """
        0:[device_type=pc] yes=1,no=2
        1:leaf=0.1
        2:leaf=0.2
    """
    parsed_tree = parse_tree(one_node_tree)

    assert parsed_tree == {
        Condition("device_type", "pc", is_equal=True): {
            True: Leaf(0.1),
            False: Leaf(0.2),
        }
    }


def test_should_handle_inequalities():
    inequality_tree = """
        0:[device_type!=pc] yes=1,no=2
        1:leaf=0.1
        2:leaf=0.2
    """
    assert parse_tree(inequality_tree) == {
        Condition("device_type", "pc", is_equal=False): {
            True: Leaf(0.1),
            False: Leaf(0.2),
        }
    }


def test_should_read_nested_node_tree():
    nested_node_tree = """
        0:[device_type=pc] yes=1,no=2
        1:[device_type=mobile] yes=3,no=4
        2:leaf=0.2
        3:leaf=0.3
        4:leaf=0.4
    """
    assert parse_tree(nested_node_tree) == {
        Condition("device_type", "pc", is_equal=True): {
            True: {
                Condition("device_type", "mobile", is_equal=True): {
                    True: Leaf(0.3),
                    False: Leaf(0.4),
                }
            },
            False: Leaf(0.2),
        }
    }


def test_should_log_empty_lines(caplog):
    caplog.set_level(10)

    empty_line_tree = """
        0:[device_type=pc] yes=1,no=2

        1:leaf=0.0
        2:leaf=1.0
    """
    parse_tree(empty_line_tree)
    assert "Skipping empty line: 0" in caplog.text
    assert "Skipping empty line: 2" in caplog.text


def test_should_skip_empty_lines():
    empty_line_tree = """
        0:[device_type=pc] yes=1,no=2

        1:leaf=0.0
        2:leaf=1.0
    """
    equivalent_tree = """0:[device_type=pc] yes=1,no=2
        1:leaf=0.0
        2:leaf=1.0
    """
    assert parse_tree(empty_line_tree) == parse_tree(equivalent_tree)


def test_should_parse_or_condition_as_nested_not_and():
    tree = """
        0:[device_type=pc||or||os=linux] yes=2,no=3
        2:leaf=0.1
        3:leaf=0.2
    """
    parsed_tree = parse_tree(tree)

    assert parsed_tree == {
        Condition("device_type", "pc", is_equal=True): {
            True: Leaf(0.1),
            False: {
                Condition("os", "linux", is_equal=True): {
                    True: None,
                    False: Leaf(0.2),
                }
            },
        },
        Condition("os", "linux", is_equal=True): {
            True: Leaf(0.1),
            False: None,
        },
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
    """
    We keep this test as a demonstration of how we could handle value constraints on leaves.
    """
    impossible_range_tree = f"""
        0:[device_type=pc] yes=1,no=2
        1:leaf=0.0
        2:leaf={threshold_impossible_leaf_value}
    """
    with expected_behavior:
        parse_tree(impossible_range_tree)

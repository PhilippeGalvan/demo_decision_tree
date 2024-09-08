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
        4:leaf=2.0
    """
    assert tree_parser(nested_node_tree) == {
        "0": Node({Condition("device_type", "pc", is_equal=True)}, "1", "2"),
        "1": Node({Condition("device_type", "mobile", is_equal=True)}, "3", "4"),
        "2": Leaf(0.0),
        "3": Leaf(1.0),
        "4": Leaf(2.0),
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
        2:leaf=2.0
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
        "2": Leaf(2.0),
    }

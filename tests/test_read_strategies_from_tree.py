from src.main import Condition, Leaf, Strategy, read_strategies_from_tree


def test_should_read_strategy_from_one_node_tree():
    one_node_tree = {
        Condition("device_type", "pc", is_equal=True): {
            True: Leaf(1.0),
            False: Leaf(1.0),
        },
    }

    strategies = read_strategies_from_tree(one_node_tree)

    assert strategies == {
        Strategy((Condition("device_type", "pc", is_equal=True),), Leaf(1.0)),
        Strategy((Condition("device_type", "pc", is_equal=False),), Leaf(1.0)),
    }


def test_should_read_strategy_from_nested_node_tree():
    two_node_tree = {
        Condition("device_type", "pc", is_equal=True): {
            True: {
                Condition("device_type", "mobile", is_equal=True): {
                    True: Leaf(1.0),
                    False: Leaf(0.5),
                },
            },
            False: Leaf(0.0),
        },
    }

    strategies = read_strategies_from_tree(two_node_tree)

    assert strategies == {
        Strategy(
            (
                Condition("device_type", "pc", is_equal=True),
                Condition("device_type", "mobile", is_equal=True),
            ),
            Leaf(1.0),
        ),
        Strategy(
            (
                Condition("device_type", "pc", is_equal=True),
                Condition("device_type", "mobile", is_equal=False),
            ),
            Leaf(0.5),
        ),
        Strategy((Condition("device_type", "pc", is_equal=False),), Leaf(0.0)),
    }

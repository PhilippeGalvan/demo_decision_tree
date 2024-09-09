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


def test_should_ignore_always_false_strategies_when_same_feature_and_value_with_opposite_statement():
    always_false_strategy_tree = {
        Condition("device_type", "pc", is_equal=True): {
            True: {
                Condition("device_type", "pc", is_equal=False): {
                    True: Leaf(1.0),
                    False: None,
                },
            },
            False: None,
        },
    }

    strategies = read_strategies_from_tree(always_false_strategy_tree)

    assert strategies == set()


def test_should_ignore_always_false_strategies_when_same_feature_and_equality_on_different_values():
    always_false_strategy_tree = {
        Condition("device_type", "pc", is_equal=True): {
            True: {
                Condition("device_type", "mobile", is_equal=True): {
                    True: Leaf(1.0),
                    False: None,
                },
            },
            False: None,
        },
    }

    strategies = read_strategies_from_tree(always_false_strategy_tree)

    assert strategies == set()

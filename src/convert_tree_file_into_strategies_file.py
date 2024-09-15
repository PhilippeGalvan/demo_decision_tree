import argparse
from pathlib import Path

from src.tree_to_strategies.app import convert_tree_to_strategies


def main(tree_file_path: Path, strategies_file_path: Path) -> None:
    with open(tree_file_path) as f:
        tree = f.read()

    strategies = convert_tree_to_strategies(tree)

    with open(strategies_file_path, "w") as f:
        # This is for the sake of output consistency at the expense of some memory
        serialized_strategies = sorted(
            strategy.to_human_readable_format() for strategy in strategies
        )
        for strategy in serialized_strategies:
            f.write(strategy)
            f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tree_file_path", type=Path)
    parser.add_argument("strategies_file_path", type=Path)
    args = parser.parse_args()

    main(args.tree_file_path, args.strategies_file_path)

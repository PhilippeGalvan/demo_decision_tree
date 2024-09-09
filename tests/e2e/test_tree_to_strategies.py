from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from src.main import main

cwd = Path(__file__).parent


@pytest.fixture
def temp_output_file():
    with NamedTemporaryFile("w") as f:
        yield Path(f.name)


@pytest.fixture
def temp_file_factory():
    with NamedTemporaryFile("w") as f:

        def _temp_file_factory(content: str):
            f.write(content)
            f.seek(0)
            return Path(f.name)

        yield _temp_file_factory


def test_should_convert_complex_tree_file_to_strategies_file(temp_output_file):
    exemple_tree_file = cwd.joinpath("tree_to_convert__288_29.txt")

    main(exemple_tree_file, temp_output_file)

    with open(temp_output_file) as f:
        strategies = f.read()

    assert strategies == ""


def test_should_format_1_node_strategy_to_expected_format(
    temp_output_file: Path, temp_file_factory
):
    exemple_tree_file = temp_file_factory(
        # fmt: off
        (
            "0:[device_type=pc] yes=1,no=2\n"
            "   1:leaf=0.1\n"
            "   2:leaf=0.2\n"
        )
        # fmt: on
    )

    expected_output = (
        # fmt: off
        "device_type!=pc : 0.2\n"
        "device_type=pc : 0.1\n"
        # fmt: on
    )

    main(exemple_tree_file, temp_output_file)

    with open(temp_output_file) as f:
        strategies = f.read()

    assert strategies == expected_output


def test_should_format_nested_strategy_to_expected_format(
    temp_output_file: Path, temp_file_factory
):
    exemple_tree_file = temp_file_factory(
        # fmt: off
        (
            "0:[device_type=pc] yes=1,no=2\n"
            "   1:[device_type=mobile] yes=3,no=4\n"
            "       3:leaf=0.3\n"
            "       4:leaf=0.4\n"
            "   2:leaf=0.2\n"
        )
        # fmt: on
    )

    expected_output = (
        # fmt: off
        "device_type!=pc : 0.2\n"
        "device_type=pc & device_type!=mobile : 0.4\n"
        "device_type=pc & device_type=mobile : 0.3\n"
        # fmt: on
    )

    main(exemple_tree_file, temp_output_file)

    with open(temp_output_file) as f:
        strategies = f.read()

    assert strategies == expected_output


def test_should_format_or_strategy_to_expected_format(
    temp_output_file: Path, temp_file_factory
):
    exemple_tree_file = temp_file_factory(
        # fmt: off
        (
            "0:[device_type=pc||or||support=mobile] yes=1,no=2\n"
            "   1:leaf=0.1\n"
            "   2:leaf=0.2\n"
        )
        # fmt: on
    )

    expected_output = (
        # fmt: off
        "device_type!=pc & support!=mobile : 0.2\n"
        "device_type=pc : 0.1\n"
        "support=mobile : 0.1\n"
        # fmt: on
    )

    main(exemple_tree_file, temp_output_file)

    with open(temp_output_file) as f:
        strategies = f.read()

    assert strategies == expected_output

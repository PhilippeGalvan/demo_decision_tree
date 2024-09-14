# Decision Tree to strategies transformer

## Introduction
The purpose of this tool is to convert a decision tree to the format illustrated in tests to strategies as shown in the tests

## Prerequisites
- Python >= 3.12
- Poetry >= 1.7.1

## Installation
1. Clone the repository and move to the project directory
```bash
git clone git@github.com:PhilippeGalvan/demo_decision_tree.git
cd demo_decision_tree
```

2. Install the dependencies
```bash
poetry env use 3.12
poetry install
```

## Tests
Tests are available in docstrings at doctest format for local unit tests as well as in tests for more complex tests.
```bash
poetry run pytest --doctest-modules
```

## Usage
```bash
poetry run python main.py
```

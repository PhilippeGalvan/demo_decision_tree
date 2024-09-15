# Decision Tree to strategies transformer

## Introduction
The purpose of this tool is to convert a decision tree to the format illustrated in tests to strategies as shown in the tests

## Prerequisites
These prerequesites and subsequent instructions are provided in the context of a Unix-like operating system.
If using windows, adapt the following instructions accordingly.
- Unix-like operating system
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
poetry run python src/convert_tree_file_into_strategies_file.py <input_file> <output_file>
```

## Demo
```bash
mkdir -p demo/outputs/
echo "0:[device_type=pc||or||browser=7] yes=2,no=1
	2:[os_family=5] yes=6,no=5
		6:[browser=8] yes=12,no=11
			12:[language=2] yes=20,no=19
				20:leaf=0.000559453
				19:leaf=0.000594593
			11:[size=300x600] yes=18,no=17
				18:leaf=0.000597397
				17:leaf=0.00063461
		5:[browser=8||or||browser=5] yes=10,no=9
			10:leaf=0.000625534
			9:[position=2] yes=16,no=15
				16:leaf=0.00066727
				15:leaf=0.000708484
	1:[browser=8] yes=4,no=3
		4:leaf=0.000881108
		3:[os_family=5] yes=8,no=7
			8:leaf=0.000842268
			7:[region=FR:A5] yes=14,no=13
				14:leaf=0.000939982
				13:leaf=0.000999001
" > demo/provided_tree.txt
poetry run python src/convert_tree_file_into_strategies_file.py demo/provided_tree.txt demo/outputs/strategies.txt
```

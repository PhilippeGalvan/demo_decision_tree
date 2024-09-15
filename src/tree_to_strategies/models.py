from collections import defaultdict
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Condition:
    feature: str
    value: str
    is_equal: bool

    @classmethod
    def from_string(cls, string: str) -> Self:
        """
        Create a Condition from a string.

        >>> Condition.from_string("device_type=pc")
        Condition(feature='device_type', value='pc', is_equal=True)
        """
        equality_per_operator = {
            "=": True,
            "!=": False,
        }

        operator = "="
        if "!=" in string:
            operator = "!="

        feature, value = string.split(operator)
        return cls(feature, value, equality_per_operator[operator])

    def to_strategy_format(self) -> str:
        """
        Convert a condition to a strategy format.

        >>> Condition("device_type", "pc", is_equal=True).to_strategy_format()
        'device_type=pc'
        """
        operator = "="
        if not self.is_equal:
            operator = "!="

        return f"{self.feature}{operator}{self.value}"


@dataclass(frozen=True, slots=True)
class Leaf:
    value: float

    @classmethod
    def from_standardized_string(cls, definition: str) -> Self:
        """
        Create a Leaf from a standardized string.

        >>> Leaf.from_standardized_string("0:leaf=0.0")
        Leaf(value=0.0)
        """
        _, value = definition.split(":leaf=")
        return cls(float(value))

    def __post_init__(self):
        if not 0 <= self.value <= 1:
            raise ValueError(f"Invalid leaf value: {self.value}, must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Node:
    eligible_conditions: tuple[Condition, ...]
    yes: str
    no: str

    @classmethod
    def from_standardized_string(cls, definition: str) -> Self:
        """
        Create a Node from a standardized string.

        >>> Node.from_standardized_string("0:[device_type=pc] yes=1,no=2")
        Node(eligible_conditions=(Condition(feature='device_type', value='pc', is_equal=True),), yes='1', no='2')
        """
        raw_condition, branches = definition.split(":[", 1)[1].split("] ", 1)

        yes, no = branches.split(",")
        yes = yes.removeprefix("yes=").strip()
        no = no.removeprefix("no=").strip()

        raw_conditions = [raw_condition]
        if "||or||" in definition:
            raw_conditions = raw_condition.split("||or||")

        conditions = tuple(
            Condition.from_string(raw_condition) for raw_condition in raw_conditions
        )
        return cls(conditions, yes, no)


@dataclass(frozen=True, slots=True)
class Strategy:
    conditions: tuple[Condition, ...]
    value: Leaf

    def to_human_readable_format(self) -> str:
        """
        Convert a strategy to a human readable format.

        >>> Strategy(
        ...     (Condition("device_type", "pc", is_equal=True),),
        ...     Leaf(1.0),
        ... ).to_human_readable_format()
        'device_type=pc : 1.0'
        >>> Strategy(
        ...     (Condition("device_type", "pc", is_equal=True), Condition("os", "linux", is_equal=True)),
        ...     Leaf(0.1),
        ... ).to_human_readable_format()
        'device_type=pc & os=linux : 0.1'
        """
        formated_condition = " & ".join(
            condition.to_strategy_format() for condition in self.conditions
        )
        return f"{formated_condition} : {self.value.value}"

    @property
    def is_not_always_false(self) -> bool:
        # This grouping by feature is O(n2) reduces the number of comparisons only to the features having multiple conditions
        conditions_grouped_by_feature: dict[str, list[Condition]] = defaultdict(list)
        for condition in self.conditions:
            conditions_grouped_by_feature[condition.feature].append(condition)

        for feature_conditions in conditions_grouped_by_feature.values():
            if len(feature_conditions) == 1:
                continue

            for index, condition_pointer in enumerate(feature_conditions):
                for condition_evaluated in feature_conditions[index + 1 :]:
                    has_same_feature_equality_on_different_values = (
                        condition_pointer.feature == condition_evaluated.feature
                        and condition_pointer.value != condition_evaluated.value
                        and (
                            condition_pointer.is_equal
                            is condition_evaluated.is_equal
                            is True
                        )
                    )

                    has_same_feature_inequality_on_same_value = (
                        condition_pointer.feature == condition_evaluated.feature
                        and condition_pointer.value == condition_evaluated.value
                        and condition_pointer.is_equal
                        is not condition_evaluated.is_equal
                    )

                    if (
                        has_same_feature_equality_on_different_values
                        or has_same_feature_inequality_on_same_value
                    ):
                        return False
        return True

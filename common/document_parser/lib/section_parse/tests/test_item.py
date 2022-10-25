from typing import Callable
from unittest import TestCase


class TestItem:
    def __init__(self, inputs, expected_output):
        self.inputs = inputs
        self.expected_output = expected_output
        self.fail_msg = ""

    def verify_output(self):
        self.verify_type()
        self.test_obj.assertEqual(
            self.actual_output,
            self.expected_output,
            self.fail_msg
            + f" Input was {self.inputs}. Expected output was `{self.expected_output}` but actual output was `{self.actual_output}`.",
        )

    def verify_type(self):
        self._get_actual_output()
        actual_type = type(self.actual_output)
        if type(self.expected_output) == type:
            expected_type = self.expected_output
        else:
            expected_type = type(self.expected_output)
        self.test_obj.assertEqual(
            actual_type,
            expected_type,
            self.fail_msg
            + f" Output should be type `{(expected_type)}` but was "
            f"`{actual_type}`. Input was {self.inputs}.",
        )

    def set_func(self, func: Callable) -> None:
        self.func = func
        self.fail_msg = f"Failure for `{self.func.__name__}()`."

    def set_test_obj(self, test_obj: TestCase) -> None:
        self.test_obj = test_obj

    def _get_actual_output(self):
        if not hasattr(self, "test_obj"):
            raise AttributeError(
                "TestItem `test_obj` attribute has not been assigned. Assign "
                "it with set_test_obj()."
            )

        if not hasattr(self, "func"):
            raise AttributeError(
                "TestItem `func` attribute has not been assigned. Assign it "
                "with set_func()."
            )

        if not hasattr(self, "actual_output"):
            self.actual_output = self.func(*self.inputs)

        return self.actual_output

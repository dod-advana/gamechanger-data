"""Helper functions for tests."""

from unittest import TestCase
from typing import Union


def verify_type(test_obj: TestCase, expected_type, actual_type, fail_msg: str = "") -> None:
    test_obj.assertEqual(
        actual_type,
        expected_type,
        fail_msg + f" Output should be type `{(expected_type)}` but was `{actual_type}`.",
    )

# TODO: docstring
def verify_output(
    test_obj: TestCase, expected_output, actual_output, fail_msg: str = ""
) -> None:
    """Verify that the expected output has the same type and value as the
    actual output."""
    expected_type = type(expected_output)
    actual_type = type(actual_output)
    verify_type(test_obj, actual_type, expected_type, fail_msg)

    test_obj.assertEqual(
        actual_output,
        expected_output,
        fail_msg
        + f" Expected output was `{expected_output}` but actual output was `{actual_output}`.",
    )


def make_fail_msg(func_name: str, input_: Union[str, None]) -> str:
    msg = f"Failure for `{func_name}`."
    if input_ is not None:
        msg += f"Input was: `{input_}.`"
    return msg


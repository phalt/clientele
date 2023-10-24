import pytest

from clientele.generators.standard import utils


@pytest.mark.parametrize(
    "input,expected_output",
    [
        ("Lowercase", "lowercase"),
        ("bad-string", "bad_string"),
        (">badstring", "badstring"),
        ("FooBarBazz", "foo_bar_bazz"),
        ("RETAIN_ALL_UPPER", "RETAIN_ALL_UPPER"),
        ("RETAINALLUPPER", "RETAINALLUPPER"),
    ],
)
def test_snake_case_prop(input, expected_output):
    assert utils.snake_case_prop(input_str=input) == expected_output

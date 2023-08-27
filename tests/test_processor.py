import pytest

from obfuscator import processor


# Test for processor.re_static_variable
@pytest.mark.parametrize("line,expected_name,expected_type", [
    ("static bool updateBaseline;", "updateBaseline", "bool"),
    ("static bool updateBasel", None, None),
    ("static bool updateBaseline", None, None),
    ("static bool isNewPmValue = false;", "isNewPmValue", "bool"),
    ("static constexpr auto Identity = [](auto i) { return i; };", "Identity", "constexpr auto"),
    ("static const uint8_t PM_ACCURACY = 10;", "PM_ACCURACY", "const uint8_t"),
])
def test_re_static_variable(line, expected_name, expected_type):
    match = processor.re_static_variable.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match.group("var_name") == expected_name
        assert match.group("var_type") == expected_type

def test_re_c_function():
    assert processor.re_c_function.match("void foo() {") is not None
    assert processor.re_c_function.match("void foo()") is None

    match = processor.re_c_function.match("void foo() {")
    assert match.group("var_name") == "foo"
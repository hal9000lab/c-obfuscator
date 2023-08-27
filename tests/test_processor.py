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
    ("static const double AMBIENT_NOISE_RATIO = 10; // TODO: tune this ratio", "AMBIENT_NOISE_RATIO", "const double"),
    ("#include <vector>", None, None),
    ("'static const vector<uint8_t> SAMPLE_TO_ENOUGH_DATA_DIFFS = {1, 2, 3};", "SAMPLE_TO_ENOUGH_DATA_DIFFS", "const vector<uint8_t>"),
])
def test_re_static_variable(line, expected_name, expected_type):
    match = processor.re_static_variable.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match.group("var_name") == expected_name
        assert match.group("var_type") == expected_type


@pytest.mark.parametrize("line,expected_name,expected_type", [
    ("bool updateBaseline(int a);", "updateBaseline", "bool"),
    ("bool updateBasel;", None, None),
    ("#include <vector>", None, None),
])
def test_re_c_function(line, expected_name, expected_type):
    match = processor.re_c_function.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match.group("func_name") == expected_name
        assert match.group("func_type") == expected_type

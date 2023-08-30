import re

import pytest

from obfuscator import parser


# Test for processor.re_static_variable
@pytest.mark.parametrize("line,expected_name,expected_type", [
    ("static bool updateBaseline;", "updateBaseline", "bool"),
    ("static bool updateBasel", None, None),
    ("static bool updateBaseline", None, None),
    ("static bool isNewPmValue = false;", "isNewPmValue", "bool"),
    ("static constexpr auto Identity = [](auto i) { return i; };", "Identity", "constexpr auto"),
    ("static const uint8_t PM = 10;", "PM", "const uint8_t"),
    ("static const double AMB = 10; // TODO: tune this ratio", "AMB", "const double"),
    ("#include <vector>", None, None),
    ("static const vector<uint8_t> SAMPLE = {1, 2, 3};", "SAMPLE", "const vector<uint8_t>"),
    ("typedef struct SmokeData {", None, None),
    ("static const char *FILENAME = \"baseline_calib.csv\";", "FILENAME", "const char"),
])
def test_re_static_variable(line, expected_name, expected_type):
    match = parser.re_static_variable.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match is not None
        assert match.group("var_name") == expected_name
        assert match.group("var_type") == expected_type


@pytest.mark.parametrize("line,expected_name,expected_type", [
    ("bool updateBaseline(int a);", "updateBaseline", "bool"),
    ("bool updateBasel;", None, None),
    ("#include <vector>", None, None),
])
def test_re_c_function(line, expected_name, expected_type):
    match = parser.re_c_function.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match.group("func_name") == expected_name
        assert match.group("func_type") == expected_type


@pytest.mark.parametrize("line,expected_name,expected_type", [
    ("static bool updateBaseline;", None, None),
    ("static bool updateBasel", None, None),
    ("static bool updateBaseline", None, None),
    ("bool isNewPmValue = false;", None, None),
    ("static constexpr auto Identity = [](auto i) { return i; };", None, None),
    ("static const uint8_t PM = 10;", None, None),
    ("const double AMB = 10; // TODO: tune this ratio", "AMB", "double"),
    ("    const double AMB = 10; // TODO: tune this ratio", None, None),
    ("#include <vector>", None, None),
    ("static const vector<uint8_t> SAMPLE = {1, 2, 3};", None, None),
    ("typedef struct SmokeData {", None, None),
])
def test_re_const_variable(line, expected_name, expected_type):
    match = parser.re_const_variable.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match is not None
        assert match.group("var_name") == expected_name
        assert match.group("var_type") == expected_type


@pytest.mark.parametrize("line,expected_name", [
    ("class ABC {", "ABC")
])
def test_re_cpp_class_name(line, expected_name):
    match = parser.re_cpp_class_name.match(line)
    if expected_name is None:
        assert match is None
    else:
        assert match is not None
        assert match.group("class_name") == expected_name

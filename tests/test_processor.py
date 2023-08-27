import pytest

from obfuscator import processor


# Test for processor.re_static_variable
def test_re_static_variable():
    assert processor.re_static_variable.match("static bool updateBaseline;") is not None
    assert processor.re_static_variable.match("static bool updateBasel") is None

    match = processor.re_static_variable.match("static bool updateBaseline;")
    assert match.group("var_type") == "bool"
    assert match.group("var_name") == "updateBaseline"

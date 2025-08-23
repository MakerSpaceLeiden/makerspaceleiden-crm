import re

import pytest

from makerspaceleiden.converters import FloatUrlParameterConverter


@pytest.fixture
def converter():
    """Fixture providing a FloatUrlParameterConverter instance"""
    return FloatUrlParameterConverter()


class TestFloatUrlParameterConverter:
    def test_to_python_integer(self, converter):
        """Test converting integer string to float"""
        result = converter.to_python("42")
        assert result == 42.0
        assert isinstance(result, float)

    def test_to_python_float(self, converter):
        """Test converting float string to float"""
        result = converter.to_python("3.14")
        assert result == 3.14
        assert isinstance(result, float)

    def test_to_python_zero(self, converter):
        """Test converting zero to float"""
        result = converter.to_python("0")
        assert result == 0.0
        assert isinstance(result, float)

    def test_to_python_decimal_zero(self, converter):
        """Test converting decimal zero to float"""
        result = converter.to_python("0.0")
        assert result == 0.0
        assert isinstance(result, float)

    def test_to_python_large_number(self, converter):
        """Test converting large number to float"""
        result = converter.to_python("123456.789")
        assert result == 123456.789
        assert isinstance(result, float)

    def test_to_python_invalid_string(self, converter):
        """Test that invalid strings raise ValueError"""
        with pytest.raises(ValueError):
            converter.to_python("not_a_number")

    def test_to_python_empty_string(self, converter):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError):
            converter.to_python("")

    def test_to_python_negative_number(self, converter):
        """Test that negative numbers are accepted by to_python (regex only affects URL routing)"""
        result = converter.to_python("-3.14")
        assert result == -3.14
        assert isinstance(result, float)

    def test_to_python_multiple_dots(self, converter):
        """Test that strings with multiple dots raise ValueError"""
        with pytest.raises(ValueError):
            converter.to_python("3.14.159")

    def test_to_url_integer(self, converter):
        """Test converting integer to URL string"""
        result = converter.to_url(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_to_url_float(self, converter):
        """Test converting float to URL string"""
        result = converter.to_url(3.14)
        assert result == "3.14"
        assert isinstance(result, str)

    def test_to_url_zero(self, converter):
        """Test converting zero to URL string"""
        result = converter.to_url(0.0)
        assert result == "0.0"
        assert isinstance(result, str)

    def test_to_url_large_number(self, converter):
        """Test converting large number to URL string"""
        result = converter.to_url(123456.789)
        assert result == "123456.789"
        assert isinstance(result, str)

    def test_regex_pattern_matches_integers(self, converter):
        """Test that regex pattern matches integer strings"""
        pattern = converter.regex
        assert re.fullmatch(pattern, "42") is not None
        # Note: "0" doesn't match because regex requires digits after optional dot
        assert re.fullmatch(pattern, "0") is None
        assert re.fullmatch(pattern, "123456") is not None

    def test_regex_pattern_matches_floats(self, converter):
        """Test that regex pattern matches float strings"""
        pattern = converter.regex
        assert re.fullmatch(pattern, "3.14") is not None
        assert re.fullmatch(pattern, "0.0") is not None
        assert re.fullmatch(pattern, "123456.789") is not None

    def test_regex_pattern_rejects_invalid_strings(self, converter):
        """Test that regex pattern rejects invalid strings"""
        pattern = converter.regex
        assert re.fullmatch(pattern, "abc") is None
        assert re.fullmatch(pattern, "") is None
        assert re.fullmatch(pattern, "-3.14") is None
        assert re.fullmatch(pattern, "3.14.159") is None
        assert re.fullmatch(pattern, "3.") is None
        assert re.fullmatch(pattern, ".14") is None
        assert (
            re.fullmatch(pattern, "0") is None
        )  # Current regex doesn't match single "0"

    @pytest.mark.parametrize("value", ["42", "3.14", "0", "0.0", "123.456"])
    def test_roundtrip_conversion(self, converter, value):
        """Test that to_python and to_url are inverse operations"""
        python_value = converter.to_python(value)
        url_value = converter.to_url(python_value)
        # Note: We can't guarantee exact string match due to float representation
        # but we can ensure the values are numerically equivalent
        assert float(url_value) == float(value)

    @pytest.mark.parametrize(
        "invalid_input,expected_exception",
        [
            ("not_a_number", ValueError),
            ("", ValueError),
            ("3.14.159", ValueError),
            ("abc123", ValueError),
        ],
    )
    def test_to_python_error_cases(self, converter, invalid_input, expected_exception):
        """Test various error cases for to_python method"""
        with pytest.raises(expected_exception):
            converter.to_python(invalid_input)

    def test_to_python_edge_cases_that_work(self, converter):
        """Test edge cases that actually work with Python's float() function"""
        # These don't match the regex but float() can parse them
        assert converter.to_python("-3.14") == -3.14
        assert converter.to_python("3.") == 3.0
        assert converter.to_python(".14") == 0.14

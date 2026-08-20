"""Tests for analytics CLI commands."""

from devpub.cli.analytics import (
    _downsample,
    _extract_total,
    _format_num,
    _parse_period,
    _short_date,
    _sparkline,
    _trend_indicator,
    _value_to_color,
)


class TestFormatNum:
    def test_small_number(self):
        assert _format_num(42) == "42"

    def test_thousands(self):
        assert _format_num(1500) == "1.5K"

    def test_millions(self):
        assert _format_num(2_500_000) == "2.5M"

    def test_zero(self):
        assert _format_num(0) == "0"

    def test_exact_thousand(self):
        assert _format_num(1000) == "1.0K"


class TestExtractTotal:
    def test_nested_dict(self):
        assert _extract_total({"total": 5000, "average_read_time": 306}) == 5000

    def test_flat_integer(self):
        assert _extract_total(246454) == 246454

    def test_float_value(self):
        assert _extract_total(3.14) == 3

    def test_none_value(self):
        assert _extract_total(None) == 0

    def test_empty_dict(self):
        assert _extract_total({}) == 0

    def test_string_value(self):
        assert _extract_total("invalid") == 0


class TestParsePeriod:
    def test_days(self):
        assert _parse_period("7d") == 7
        assert _parse_period("30d") == 30
        assert _parse_period("90d") == 90

    def test_weeks(self):
        assert _parse_period("2w") == 14
        assert _parse_period("4w") == 28

    def test_months(self):
        assert _parse_period("1m") == 30
        assert _parse_period("3m") == 90

    def test_default_on_invalid(self):
        assert _parse_period("abc") == 30
        assert _parse_period("") == 30

    def test_case_insensitive(self):
        assert _parse_period("7D") == 7
        assert _parse_period("2W") == 14


class TestShortDate:
    def test_iso_date(self):
        assert _short_date("2026-07-15") == "Jul 15"

    def test_iso_datetime(self):
        assert _short_date("2026-07-15T10:30:00Z") == "Jul 15"

    def test_empty_string(self):
        assert _short_date("") == ""

    def test_none(self):
        assert _short_date(None) == ""

    def test_short_string(self):
        assert _short_date("Jul") == "Jul"


class TestDownsample:
    def test_basic_downsampling(self):
        values = [10, 20, 30, 40, 50, 60]
        labels = ["a", "b", "c", "d", "e", "f"]
        new_vals, new_labels = _downsample(values, labels, 3)
        assert len(new_vals) == 3
        assert len(new_labels) == 3
        # First chunk: (10+20)/2 = 15
        assert new_vals[0] == 15

    def test_no_downsampling_needed(self):
        values = [1, 2, 3]
        labels = ["a", "b", "c"]
        new_vals, new_labels = _downsample(values, labels, 10)
        # Should still work (chunk_size=1)
        assert len(new_vals) == 3

    def test_single_value(self):
        values = [100]
        labels = ["x"]
        new_vals, new_labels = _downsample(values, labels, 5)
        assert new_vals == [100]
        assert new_labels == ["x"]


class TestValueToColor:
    def test_low_value(self):
        color = _value_to_color(0.1)
        assert color.startswith("rgb(50,")

    def test_mid_value(self):
        color = _value_to_color(0.5)
        assert "200" in color

    def test_high_value(self):
        color = _value_to_color(0.8)
        assert "220" in color

    def test_peak_value(self):
        color = _value_to_color(0.98)
        assert color == "rgb(255,200,0)"

    def test_zero(self):
        color = _value_to_color(0.0)
        assert color.startswith("rgb(50,")

    def test_one(self):
        color = _value_to_color(1.0)
        assert color == "rgb(255,200,0)"


class TestSparkline:
    def test_basic(self):
        result = _sparkline([0, 50, 100, 50, 0])
        assert len(result) == 5
        assert result[0] == "\u2581"
        assert result[2] == "\u2588"

    def test_all_same(self):
        result = _sparkline([50, 50, 50])
        assert len(result) == 3

    def test_empty(self):
        assert _sparkline([]) == ""

    def test_single_value(self):
        result = _sparkline([100])
        assert len(result) == 1
        assert result == "\u2588"

    def test_zeros(self):
        result = _sparkline([0, 0, 0])
        assert len(result) == 3


class TestTrendIndicator:
    def test_trending_up(self):
        values = [10, 10, 10, 10, 10, 10, 10, 50, 50, 50, 50, 50, 50, 50]
        result = _trend_indicator(values)
        assert "\u2197" in result
        assert "+" in result

    def test_trending_down(self):
        values = [50, 50, 50, 50, 50, 50, 50, 10, 10, 10, 10, 10, 10, 10]
        result = _trend_indicator(values)
        assert "\u2198" in result

    def test_stable(self):
        values = [50, 50, 50, 50, 50, 50, 50, 51, 50, 50, 50, 50, 50, 50]
        result = _trend_indicator(values)
        assert "\u2192" in result

    def test_short_data(self):
        values = [10, 20, 30]
        result = _trend_indicator(values)
        assert isinstance(result, str)

    def test_very_short_data(self):
        values = [10, 20]
        result = _trend_indicator(values)
        assert result == ""

    def test_previous_zero(self):
        values = [0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50]
        result = _trend_indicator(values)
        assert "new" in result

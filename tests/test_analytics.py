"""Tests for analytics CLI commands."""

from devpub.cli.analytics import (
    _downsample,
    _extract_total,
    _format_num,
    _parse_period,
    _short_date,
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

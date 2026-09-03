"""Tests for the comments CLI helpers."""

from devpub.cli.comments import _count, _html_to_text


class TestHtmlToText:
    def test_strips_tags(self):
        assert _html_to_text("<p>Hello <strong>world</strong></p>") == "Hello world"

    def test_unescapes_entities(self):
        assert _html_to_text("<p>a &amp; b &lt; c</p>") == "a & b < c"

    def test_paragraphs_become_newlines(self):
        result = _html_to_text("<p>First</p><p>Second</p>")
        assert result == "First\nSecond"

    def test_br_becomes_newline(self):
        assert _html_to_text("one<br>two") == "one\ntwo"

    def test_empty_input(self):
        assert _html_to_text("") == ""
        assert _html_to_text(None) == ""

    def test_collapses_blank_lines(self):
        # Multiple block closes should not produce runs of blank lines.
        result = _html_to_text("<p>a</p><p></p><p>b</p>")
        assert "\n\n" not in result
        assert result == "a\nb"


class TestCount:
    def test_flat(self):
        comments = [{"children": []}, {"children": []}]
        assert _count(comments) == 2

    def test_nested(self):
        comments = [
            {
                "children": [
                    {"children": []},
                    {"children": [{"children": []}]},
                ]
            }
        ]
        # 1 top-level + 2 replies + 1 nested reply = 4
        assert _count(comments) == 4

    def test_missing_children_key(self):
        assert _count([{}, {}]) == 2

    def test_empty(self):
        assert _count([]) == 0

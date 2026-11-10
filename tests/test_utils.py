from __future__ import annotations

from datetime import date

import pytest

from xigua.utils import (
    absolute_url,
    human_date,
    is_hex_color,
    plain_text,
    reading_minutes,
    relative_url,
    slugify,
    truncate,
    unique_slug,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Hello World", "hello-world"),
        ("  多个   空格  ", "多个-空格"),
        ("Python 3.12 新特性", "python-3-12-新特性"),
        ("C++ / Rust", "c-rust"),
        ("---", "post"),
        ("", "post"),
    ],
)
def test_slugify(value: str, expected: str) -> None:
    assert slugify(value) == expected


def test_slugify_keeps_chinese_readable() -> None:
    assert slugify("我的第一篇文章") == "我的第一篇文章"


def test_unique_slug() -> None:
    used = {"post", "post-2"}
    assert unique_slug("post", used) == "post-3"
    assert unique_slug("other", used) == "other"


def test_plain_text_strips_markup_and_scripts() -> None:
    html = "<p>你好 <strong>世界</strong></p><script>alert(1)</script><p>下一段</p>"
    assert plain_text(html) == "你好 世界 下一段"


def test_truncate_does_not_cut_words() -> None:
    text = "The quick brown fox jumps over the lazy dog"
    result = truncate(text, 20)
    assert len(result) <= 21
    assert result.endswith("…")
    assert "jumps" not in result


def test_truncate_keeps_short_text() -> None:
    assert truncate("短文本", 20) == "短文本"


def test_reading_minutes_mixed_language() -> None:
    assert reading_minutes("") == 1
    assert reading_minutes("中" * 800) == 2
    assert reading_minutes("word " * 440) == 2


def test_human_date_chinese_and_english() -> None:
    day = date(2026, 2, 14)
    assert human_date(day, "zh-CN") == "2026 年 2 月 14 日"
    assert human_date(day, "en") == "Feb 14, 2026"


def test_absolute_url() -> None:
    assert absolute_url("https://example.com", "blog/post/") == "https://example.com/blog/post/"
    assert absolute_url("https://example.com/", "") == "https://example.com/"
    assert absolute_url("", "blog/post/") == "/blog/post/"
    assert absolute_url("", "") == "/"


def test_relative_url() -> None:
    assert relative_url("blog/", 0) == "blog/"
    assert relative_url("blog/", 2) == "../../blog/"
    assert relative_url("", 1) == "../"
    assert relative_url("", 0) == "./"
    assert relative_url("https://example.com", 2) == "https://example.com"
    assert relative_url("#main", 2) == "#main"


def test_is_hex_color() -> None:
    assert is_hex_color("#fff")
    assert is_hex_color("#ea580c")
    assert not is_hex_color("orange")
    assert not is_hex_color("#xyz")

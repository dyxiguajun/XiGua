"""Small, dependency-free helpers used across the generator."""

from __future__ import annotations

import html
import math
import re
import unicodedata
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import quote

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['\u2019-][A-Za-z0-9]+)*")
SLUG_RE = re.compile(r"[^\w-]+", re.UNICODE)
DASH_RE = re.compile(r"-{2,}")
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def slugify(value: object, fallback: str = "post") -> str:
    """Turn a title into a stable, readable URL segment.

    Unicode letters are preserved, which keeps Chinese titles readable. Only
    whitespace, punctuation, and symbols are collapsed into hyphens.
    """
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = SLUG_RE.sub("-", text)
    text = DASH_RE.sub("-", text).strip("-")
    return text or fallback


def unique_slug(slug: str, used: set[str]) -> str:
    """Return ``slug`` or the first available ``slug-2``, ``slug-3``, ..."""
    if slug not in used:
        return slug
    index = 2
    while f"{slug}-{index}" in used:
        index += 1
    return f"{slug}-{index}"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "tr"}:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "tr"}:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self._parts)).strip()


def plain_text(html_text: str) -> str:
    """Extract a readable plain-text version of rendered HTML."""
    parser = _TextExtractor()
    parser.feed(html_text)
    parser.close()
    return parser.text()


def truncate(text: str, limit: int = 160) -> str:
    """Trim text on a word boundary when possible, without cutting a URL."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rstrip()
    if " " in cut and not CJK_RE.search(cut[-1:]):
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:，。；：") + "…"


def reading_minutes(text: str) -> int:
    """Estimate reading time for mixed Chinese/English text."""
    cjk = len(CJK_RE.findall(text))
    words = len(WORD_RE.findall(CJK_RE.sub(" ", text)))
    minutes = cjk / 400 + words / 220
    return max(1, math.ceil(minutes))


def human_date(value: date | datetime, lang: str = "zh-CN") -> str:
    """Format a date for display, using a Chinese format for Chinese sites."""
    day = value.date() if isinstance(value, datetime) else value
    if lang.lower().startswith("zh"):
        return f"{day.year} 年 {day.month} 月 {day.day} 日"
    return day.strftime("%b %d, %Y")


def absolute_url(base: str, path: str = "") -> str:
    """Join a site base URL and a path without double slashes."""
    base = (base or "").rstrip("/")
    path = path.lstrip("/")
    if not base:
        return "/" + quote(path, safe="/") if path else "/"
    if not path:
        return base + "/"
    return base + "/" + quote(path, safe="/")


def relative_url(path: str, depth: int) -> str:
    """Build a relative URL that works from a page ``depth`` levels deep."""
    if path.startswith(("http://", "https://", "mailto:", "//", "#")):
        return path
    prefix = "../" * depth
    if not path:
        return prefix or "./"
    return prefix + path.lstrip("/")


def is_hex_color(value: str) -> bool:
    return bool(HEX_COLOR_RE.match(value.strip()))


def escape(value: object) -> str:
    """Escape text for HTML attributes or XML text."""
    return html.escape(str(value), quote=True)

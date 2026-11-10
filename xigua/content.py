"""Read Markdown posts, front matter, and derived metadata."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .config import SiteConfig
from .errors import ContentError
from .rendering import render_markdown
from .utils import plain_text, reading_minutes, slugify, truncate, unique_slug

logger = logging.getLogger("xigua.content")

FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
DATE_IN_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Post:
    title: str
    slug: str
    date: date
    tags: tuple[str, ...]
    description: str
    draft: bool
    pinned: bool
    cover: str
    source: Path
    html: str
    toc: str
    text: str
    excerpt: str
    reading_minutes: int
    path: str


def parse_front_matter(source: str, origin: Path | str = "<post>") -> tuple[dict[str, Any], str]:
    """Split a post into YAML front matter and Markdown body."""
    text = source.lstrip("\ufeff")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    raw = match.group(1)
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ContentError(f"{origin}: front matter 不是合法的 YAML：{exc}") from exc

    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ContentError(f"{origin}: front matter 必须是一个键值表。")
    return meta, text[match.end() :]


def normalize_tags(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        raise ContentError(f"tags 必须是字符串或数组，收到：{type(value).__name__}")

    tags: list[str] = []
    for item in items:
        tag = str(item).strip().lstrip("#").strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tuple(tags)


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _parse_date(value: Any, source: Path, fallback: date) -> date:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for parser in (date.fromisoformat, datetime.fromisoformat):
            try:
                parsed = parser(text)
            except ValueError:
                continue
            return parsed.date() if isinstance(parsed, datetime) else parsed
        for fmt in ("%Y/%m/%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    raise ContentError(f"{source.name}: 无法解析日期 `{value}`，请使用 YYYY-MM-DD。")


def _fallback_date(source: Path) -> date:
    match = DATE_IN_NAME_RE.match(source.stem)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass
    return datetime.fromtimestamp(source.stat().st_mtime).date()


def _title_from_body(body: str) -> str:
    match = H1_RE.search(body)
    return match.group(1).strip() if match else ""


def _title_from_name(source: Path) -> str:
    stem = DATE_IN_NAME_RE.sub("", source.stem).lstrip("-_ ")
    return stem.replace("-", " ").replace("_", " ").strip() or source.stem


def _read_text(source: Path) -> str:
    try:
        return source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContentError(f"{source.name}: 文件必须是 UTF-8 编码。") from exc
    except OSError as exc:
        raise ContentError(f"读取 {source} 失败：{exc}") from exc


def load_posts(config: SiteConfig, include_drafts: bool = False) -> list[Post]:
    """Load every Markdown file in the configured posts directory."""
    posts_dir = config.posts_dir
    if not posts_dir.exists():
        raise ContentError(f"文章目录不存在：{posts_dir}")
    if not posts_dir.is_dir():
        raise ContentError(f"文章路径不是目录：{posts_dir}")

    files = sorted(
        [path for path in posts_dir.iterdir() if path.suffix.lower() in {".md", ".markdown"}],
        key=lambda path: path.name.lower(),
    )

    posts: list[Post] = []
    used_slugs: set[str] = set()
    for source in files:
        if source.name.startswith(("_", ".")):
            continue

        raw = _read_text(source)
        meta, body = parse_front_matter(raw, source)

        fallback_date = _fallback_date(source)
        post_date = _parse_date(meta.get("date"), source, fallback_date)
        title = str(meta.get("title") or "").strip() or _title_from_body(body) or _title_from_name(source)
        if not title:
            raise ContentError(f"{source.name}: 找不到标题。请在 front matter 写 title，或用 # 标题。")

        slug_value = meta.get("slug") or title
        slug = slugify(slug_value, fallback=source.stem)
        unique = unique_slug(slug, used_slugs)
        if unique != slug:
            logger.warning("%s: slug `%s` 重复，改用 `%s`", source.name, slug, unique)
            slug = unique
        used_slugs.add(slug)

        html_text, toc = render_markdown(body)
        text = plain_text(html_text)
        description = str(meta.get("description") or "").strip()
        excerpt = truncate(description or text, 160)

        post = Post(
            title=title,
            slug=slug,
            date=post_date,
            tags=normalize_tags(meta.get("tags")),
            description=description,
            draft=_as_bool(meta.get("draft")),
            pinned=_as_bool(meta.get("pinned")),
            cover=str(meta.get("cover") or "").strip(),
            source=source,
            html=html_text,
            toc=toc,
            text=text,
            excerpt=excerpt,
            reading_minutes=reading_minutes(text),
            path=f"blog/{slug}/",
        )
        if post.draft and not include_drafts:
            continue
        posts.append(post)

    posts.sort(key=lambda post: (not post.pinned, -post.date.toordinal(), post.title.lower()))
    return posts

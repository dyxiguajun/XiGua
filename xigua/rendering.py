"""Markdown rendering and the Jinja environment."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import markdown as markdown_lib
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments.formatters import HtmlFormatter

from .config import SiteConfig
from .utils import absolute_url, human_date, relative_url, slugify

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

_EXTERNAL_LINK_RE = re.compile(r'<a\b[^>]*href="https?://[^"]*"[^>]*>', re.IGNORECASE)
_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def _add_external_attrs(match: re.Match[str]) -> str:
    tag = match.group(0)
    if "target=" in tag:
        return tag
    return tag[:-1].rstrip() + ' target="_blank" rel="noopener noreferrer">'


def _add_image_attrs(match: re.Match[str]) -> str:
    tag = match.group(0)
    suffix = " />" if tag.endswith("/>") else ">"
    body = tag[: -len(suffix)].rstrip()
    if "loading=" not in tag:
        body += ' loading="lazy"'
    if "decoding=" not in tag:
        body += ' decoding="async"'
    return body + suffix


def post_process(html_text: str) -> str:
    """Make links and images behave well without touching the Markdown source."""
    html_text = _EXTERNAL_LINK_RE.sub(_add_external_attrs, html_text)
    html_text = _IMG_RE.sub(_add_image_attrs, html_text)
    return html_text


def render_markdown(source: str) -> tuple[str, str]:
    """Render Markdown to HTML and return ``(html, table_of_contents)``."""
    md = markdown_lib.Markdown(
        extensions=["extra", "codehilite", "toc", "sane_lists"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False, "linenums": False},
            "toc": {"permalink": False, "toc_depth": "2-3", "slugify": slugify},
        },
        output_format="html5",
    )
    html_text = md.convert(source)
    toc = getattr(md, "toc", "")
    return post_process(html_text), toc


def pygments_css() -> str:
    """Return a self-contained, dark syntax-highlighting theme."""
    formatter = HtmlFormatter(style="github-dark")
    return formatter.get_style_defs(".highlight")


def create_environment(config: SiteConfig) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["datefmt"] = lambda value: human_date(value, config.lang)
    env.filters["tag_slug"] = slugify
    env.globals["today"] = date.today
    return env


class Renderer:
    """Render templates with the helpers each page needs."""

    def __init__(self, config: SiteConfig, base_url: str | None = None) -> None:
        self.config = config
        self.base_url = (base_url if base_url is not None else config.url).rstrip("/")
        self.env = create_environment(config)

    def url_for(self, href: str, depth: int) -> str:
        return relative_url(href, depth)

    def abs(self, path: str = "") -> str:
        return absolute_url(self.base_url, path)

    def render(self, template_name: str, out_path: Path, *, depth: int, use_absolute_urls: bool = False, **context: Any) -> str:
        template = self.env.get_template(template_name)
        link = self.abs if use_absolute_urls else (lambda href: self.url_for(href, depth))
        page_context = {
            "site": self.config,
            "depth": depth,
            "url_for": link,
            "abs": self.abs,
            "year": datetime.now().year,
        }
        page_context.update(context)
        html_text = template.render(**page_context)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_text, encoding="utf-8")
        return html_text

    def render_string(self, template_name: str, *, depth: int = 0, use_absolute_urls: bool = False, **context: Any) -> str:
        template = self.env.get_template(template_name)
        link = self.abs if use_absolute_urls else (lambda href: self.url_for(href, depth))
        page_context = {
            "site": self.config,
            "depth": depth,
            "url_for": link,
            "abs": self.abs,
            "year": datetime.now().year,
        }
        page_context.update(context)
        return template.render(**page_context)

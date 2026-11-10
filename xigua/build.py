"""Build the static site into an output directory."""

from __future__ import annotations

import html
import json
import logging
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from email.utils import format_datetime
from pathlib import Path
from typing import Any

from .config import SiteConfig
from .content import Post, load_posts
from .errors import BuildError
from .rendering import STATIC_DIR, Renderer, pygments_css
from .utils import slugify, unique_slug

logger = logging.getLogger("xigua.build")

ATOM_NS = "http://www.w3.org/2005/Atom"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


@dataclass(frozen=True)
class BuildResult:
    out_dir: Path
    posts: int
    tags: int
    pages: int


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_output(config: SiteConfig, out_dir: Path | None, clean: bool) -> Path:
    out = (Path(out_dir) if out_dir is not None else config.out_dir).expanduser().resolve()
    protected = {Path("/"), Path.home(), config.root}
    if out in protected:
        raise BuildError(f"拒绝把站点输出到 {out}。请换一个子目录，例如 dist/。")
    if clean and out.exists():
        if not out.is_dir():
            raise BuildError(f"输出路径不是目录：{out}")
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _copy_static(out: Path, config: SiteConfig) -> None:
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for source in sorted(STATIC_DIR.iterdir()):
        if source.is_file():
            shutil.copy2(source, assets / source.name)
    if config.static_dir.exists():
        if not config.static_dir.is_dir():
            raise BuildError(f"静态资源路径不是目录：{config.static_dir}")
        shutil.copytree(config.static_dir, out, dirs_exist_ok=True)
    _write_text(out / ".nojekyll", "")


def _write_favicon(out: Path, config: SiteConfig) -> None:
    letter = html.escape((config.title or "X")[:1])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="16" fill="{html.escape(config.accent)}"/>
  <text x="32" y="33" fill="#fff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
        font-size="30" font-weight="700" text-anchor="middle" dominant-baseline="middle">{letter}</text>
</svg>
"""
    _write_text(out / "assets" / "favicon.svg", svg)


def _tag_index(posts: list[Post]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    grouped: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            grouped.setdefault(tag, []).append(post)

    used: set[str] = set()
    tags: list[dict[str, Any]] = []
    slug_by_name: dict[str, str] = {}
    for name, tagged_posts in grouped.items():
        slug = unique_slug(slugify(name), used)
        used.add(slug)
        slug_by_name[name] = slug
        tags.append({"name": name, "slug": slug, "count": len(tagged_posts), "posts": tagged_posts})

    tags.sort(key=lambda item: (-item["count"], item["name"].lower()))
    return tags, slug_by_name


def _related(post: Post, posts: list[Post], limit: int = 3) -> list[Post]:
    scored: list[tuple[int, int, Post]] = []
    for other in posts:
        if other.slug == post.slug:
            continue
        shared = len(set(post.tags) & set(other.tags))
        if shared:
            scored.append((shared, other.date.toordinal(), other))
    scored.sort(key=lambda item: (-item[0], -item[1]))
    return [item[2] for item in scored[:limit]]


def _jsonld_post(post: Post, config: SiteConfig, url: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "datePublished": post.date.isoformat(),
        "dateModified": post.date.isoformat(),
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Person", "name": config.author or config.title},
        "publisher": {"@type": "Organization", "name": config.title},
        "description": post.description or post.excerpt,
    }
    if post.tags:
        data["keywords"] = list(post.tags)
    if post.cover:
        data["image"] = post.cover
    return data


def _jsonld_home(config: SiteConfig, url: str, posts: list[Post]) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": config.title,
        "url": url,
        "description": config.description,
        "author": {"@type": "Person", "name": config.author or config.title},
        "blog": {
            "@type": "Blog",
            "name": f"{config.title} 的文章",
            "url": url.rstrip("/") + "/blog/",
            "blogPost": [
                {"@type": "BlogPosting", "headline": post.title, "url": url.rstrip("/") + "/" + post.path}
                for post in posts[:5]
            ],
        },
    }


def _write_feed(out: Path, config: SiteConfig, posts: list[Post], renderer: Renderer) -> None:
    ET.register_namespace("atom", ATOM_NS)
    ET.register_namespace("content", CONTENT_NS)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = config.title
    ET.SubElement(channel, "link").text = renderer.abs("")
    ET.SubElement(channel, "description").text = config.description or config.title
    ET.SubElement(channel, "language").text = config.lang
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(UTC))
    ET.SubElement(channel, "generator").text = "XiGua"
    ET.SubElement(
        channel,
        f"{{{ATOM_NS}}}link",
        {"href": renderer.abs("feed.xml"), "rel": "self", "type": "application/rss+xml"},
    )

    for post in posts[:20]:
        url = renderer.abs(post.path)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post.title
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = url
        ET.SubElement(item, "pubDate").text = format_datetime(
            datetime.combine(post.date, time(8, 0), tzinfo=UTC)
        )
        ET.SubElement(item, "description").text = post.description or post.excerpt
        ET.SubElement(item, f"{{{CONTENT_NS}}}encoded").text = post.html
        for tag in post.tags:
            ET.SubElement(item, "category").text = tag

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    path = out / "feed.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _write_sitemap(out: Path, config: SiteConfig, posts: list[Post], tags: list[dict[str, Any]], renderer: Renderer) -> None:
    root = ET.Element("urlset", {"xmlns": SITEMAP_NS})
    latest = max((post.date for post in posts), default=date.today())

    def add(path: str, lastmod: date, priority: str, changefreq: str = "weekly") -> None:
        entry = ET.SubElement(root, "url")
        ET.SubElement(entry, "loc").text = renderer.abs(path)
        ET.SubElement(entry, "lastmod").text = lastmod.isoformat()
        ET.SubElement(entry, "changefreq").text = changefreq
        ET.SubElement(entry, "priority").text = priority

    add("", latest, "1.0")
    add("blog/", latest, "0.9")
    add("tags/", latest, "0.6")
    for tag in tags:
        add(f"tags/{tag['slug']}/", latest, "0.5")
    for post in posts:
        add(post.path, post.date, "0.8", "monthly")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(out / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def _write_robots(out: Path, config: SiteConfig, renderer: Renderer) -> None:
    lines = ["User-agent: *", "Allow: /"]
    if config.url:
        lines += ["", f"Sitemap: {renderer.abs('sitemap.xml')}"]
    _write_text(out / "robots.txt", "\n".join(lines) + "\n")


def build(
    config: SiteConfig,
    *,
    out_dir: Path | str | None = None,
    base_url: str | None = None,
    include_drafts: bool = False,
    clean: bool = True,
) -> BuildResult:
    """Render every page, feed, and asset for a site."""
    if not config.posts_dir.exists():
        raise BuildError(f"文章目录不存在：{config.posts_dir}。先运行 `xigua init` 或创建 posts/。")

    posts = load_posts(config, include_drafts=include_drafts)
    out = _prepare_output(config, Path(out_dir) if out_dir is not None else None, clean)
    _write_favicon(out, config)
    _write_text(out / "assets" / "pygments.css", pygments_css())
    _copy_static(out, config)

    renderer = Renderer(config, base_url)
    if not config.url and base_url is None:
        logger.warning("没有设置 site.url，RSS 和 sitemap 里的链接会是相对路径。")

    tags, _ = _tag_index(posts)
    description = config.description or config.profile.bio
    pages = 0

    # Home
    renderer.render(
        "index.html",
        out / "index.html",
        depth=0,
        title=config.title,
        description=description,
        canonical=renderer.abs(""),
        current_nav="",
        body_class="page-home",
        posts=posts[:6],
        jsonld=_jsonld_home(config, renderer.abs(""), posts),
    )
    pages += 1

    # Blog index
    renderer.render(
        "blog.html",
        out / "blog" / "index.html",
        depth=1,
        title="文章",
        description=f"{config.title} 的文章列表。",
        canonical=renderer.abs("blog/"),
        current_nav="blog/",
        posts=posts,
        tags=tags,
    )
    pages += 1

    # Posts
    for index, post in enumerate(posts):
        prev_post = posts[index + 1] if index + 1 < len(posts) else None
        next_post = posts[index - 1] if index > 0 else None
        renderer.render(
            "post.html",
            out / "blog" / post.slug / "index.html",
            depth=2,
            title=post.title,
            description=post.description or post.excerpt,
            canonical=renderer.abs(post.path),
            current_nav="blog/",
            og_type="article",
            body_class="page-post",
            post=post,
            prev=prev_post,
            next=next_post,
            related=_related(post, posts),
            jsonld=_jsonld_post(post, config, renderer.abs(post.path)),
        )
        pages += 1

    # Tags
    renderer.render(
        "tags.html",
        out / "tags" / "index.html",
        depth=1,
        title="标签",
        description=f"{config.title} 的全部标签。",
        canonical=renderer.abs("tags/"),
        current_nav="tags/",
        tags=tags,
    )
    pages += 1

    for tag in tags:
        renderer.render(
            "tag.html",
            out / "tags" / tag["slug"] / "index.html",
            depth=2,
            title=f"#{tag['name']}",
            description=f"{config.title} 中带有 #{tag['name']} 标签的文章。",
            canonical=renderer.abs(f"tags/{tag['slug']}/"),
            current_nav="tags/",
            tag=tag,
            posts=tag["posts"],
        )
        pages += 1

    # 404
    renderer.render(
        "404.html",
        out / "404.html",
        depth=0,
        use_absolute_urls=True,
        title="页面未找到",
        description="页面不存在。",
        canonical=renderer.abs("404.html"),
        current_nav="",
        body_class="page-404",
    )
    pages += 1

    _write_feed(out, config, posts, renderer)
    _write_sitemap(out, config, posts, tags, renderer)
    _write_robots(out, config, renderer)

    if config.cname:
        _write_text(out / "CNAME", config.cname.strip() + "\n")

    # A small machine-readable index, useful for custom search or integrations.
    search_index = [
        {
            "title": post.title,
            "url": renderer.abs(post.path),
            "description": post.description or post.excerpt,
            "tags": list(post.tags),
            "date": post.date.isoformat(),
        }
        for post in posts
    ]
    _write_text(out / "search-index.json", json.dumps(search_index, ensure_ascii=False, indent=2) + "\n")

    logger.info("已生成 %d 篇文章、%d 个标签、%d 个页面 -> %s", len(posts), len(tags), pages, out)
    return BuildResult(out_dir=out, posts=len(posts), tags=len(tags), pages=pages)

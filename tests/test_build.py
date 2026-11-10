from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from urllib.parse import unquote

import pytest

from tests.conftest import write_post
from xigua.build import build
from xigua.errors import BuildError


@pytest.fixture()
def built_site(config):
    write_post(
        config.root,
        "2026-01-02-hello.md",
        """
        ---
        title: "Hello"
        tags: [Python, 测试]
        description: "第一篇"
        ---

        # Hello

        这是正文，包含 `inline code`。
        """,
    )
    write_post(
        config.root,
        "2026-02-03-second.md",
        """
        ---
        title: "第二篇"
        tags: [Python]
        ---

        ## 小标题

        ```python
        print("hi")
        ```
        """,
    )
    write_post(
        config.root,
        "2026-03-04-draft.md",
        """
        ---
        title: "草稿"
        draft: true
        ---
        不该出现
        """,
    )
    return build(config, out_dir=config.root / "dist")


def test_build_writes_expected_files(built_site, config) -> None:
    out = built_site.out_dir
    assert built_site.posts == 2
    assert built_site.tags == 2
    for name in (
        "index.html",
        "blog/index.html",
        "blog/hello/index.html",
        "blog/第二篇/index.html",
        "tags/index.html",
        "tags/python/index.html",
        "tags/测试/index.html",
        "feed.xml",
        "sitemap.xml",
        "robots.txt",
        "search-index.json",
        "404.html",
        "assets/style.css",
        "assets/app.js",
        "assets/pygments.css",
        "assets/favicon.svg",
        ".nojekyll",
    ):
        assert (out / name).is_file(), name

    html = (out / "index.html").read_text(encoding="utf-8")
    assert "测试站点" in html
    assert "Hello" in html
    assert "第二篇" in html
    assert "草稿" not in html
    assert 'href="blog/hello/"' in html
    assert "https://example.com/base/" in html


def test_drafts_can_be_included(config) -> None:
    write_post(config.root, "draft.md", '---\ntitle: "D"\ndraft: true\n---\nbody')
    result = build(config, out_dir=config.root / "dist", include_drafts=True)
    assert result.posts == 1
    assert (config.root / "dist" / "blog" / "d" / "index.html").is_file()


def test_post_page_has_relative_assets_and_content(built_site, config) -> None:
    html = (config.root / "dist" / "blog" / "hello" / "index.html").read_text(encoding="utf-8")
    assert '../../assets/style.css' in html
    assert 'href="../../blog/"' in html
    assert "inline code" in html
    assert 'src="../../assets/app.js"' in html


def test_404_uses_absolute_urls(built_site, config) -> None:
    html = (config.root / "dist" / "404.html").read_text(encoding="utf-8")
    assert 'href="https://example.com/base/assets/style.css"' in html
    assert 'href="https://example.com/base/"' in html
    assert 'href="https://example.com/base/blog/"' in html


def test_external_links_and_images_are_hardened(config) -> None:
    write_post(
        config.root,
        "2026-01-01-links.md",
        """
        ---
        title: "Links"
        ---
        [Example](https://example.com) and ![pic](https://example.com/a.png)
        """,
    )
    build(config, out_dir=config.root / "dist")
    html = (config.root / "dist" / "blog" / "links" / "index.html").read_text(encoding="utf-8")
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert 'loading="lazy"' in html


def test_feed_is_valid_and_contains_posts(built_site, config) -> None:
    root = ET.parse(config.root / "dist" / "feed.xml").getroot()
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("title") == "测试站点"
    items = channel.findall("item")
    assert len(items) == 2
    assert items[0].findtext("title") == "第二篇"
    assert unquote(items[0].findtext("link")) == "https://example.com/base/blog/第二篇/"
    assert items[0].findtext("{http://purl.org/rss/1.0/modules/content/}encoded") is not None
    categories = [item.text for item in items[0].findall("category")]
    assert categories == ["Python"]


def test_sitemap_is_valid(built_site, config) -> None:
    root = ET.parse(config.root / "dist" / "sitemap.xml").getroot()
    assert root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"
    urls = [entry.findtext("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") for entry in root]
    assert "https://example.com/base/" in urls
    assert "https://example.com/base/blog/hello/" in urls


def test_search_index(built_site, config) -> None:
    data = json.loads((config.root / "dist" / "search-index.json").read_text(encoding="utf-8"))
    assert {item["title"] for item in data} == {"Hello", "第二篇"}
    assert data[0]["url"].startswith("https://example.com/base/blog/")


def test_base_url_override(config) -> None:
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(config, out_dir=config.root / "dist", base_url="http://localhost:8000")
    html = (config.root / "dist" / "index.html").read_text(encoding="utf-8")
    assert "http://localhost:8000/" in html
    robots = (config.root / "dist" / "robots.txt").read_text(encoding="utf-8")
    assert "http://localhost:8000/sitemap.xml" in robots


def test_no_url_uses_relative_links(config) -> None:
    config_path = config.config_path
    text = config_path.read_text(encoding="utf-8").replace(
        'url = "https://example.com/base"\n', ""
    )
    config_path.write_text(text, encoding="utf-8")
    from xigua.config import load_config

    local = load_config(config.root)
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(local, out_dir=config.root / "dist")
    robots = (config.root / "dist" / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap" not in robots


def test_refuses_to_overwrite_site_root(config) -> None:
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    with pytest.raises(BuildError, match="拒绝"):
        build(config, out_dir=config.root)


def test_clean_false_keeps_existing_files(config) -> None:
    out = config.root / "dist"
    out.mkdir()
    (out / "keep.txt").write_text("keep", encoding="utf-8")
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(config, out_dir=out, clean=False)
    assert (out / "keep.txt").is_file()


def test_clean_true_removes_stale_files(config) -> None:
    out = config.root / "dist"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(config, out_dir=out, clean=True)
    assert not (out / "stale.txt").exists()


def test_custom_cname(config) -> None:
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    config_path = config.config_path
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'author = "测试作者"', 'author = "测试作者"\ncname = "example.com"'
        ),
        encoding="utf-8",
    )
    from xigua.config import load_config

    build(load_config(config.root), out_dir=config.root / "dist")
    assert (config.root / "dist" / "CNAME").read_text(encoding="utf-8") == "example.com\n"


def test_site_static_files_are_copied(config) -> None:
    static = config.static_dir
    static.mkdir()
    (static / "custom.txt").write_text("custom", encoding="utf-8")
    (static / "images").mkdir()
    (static / "images" / "a.txt").write_text("a", encoding="utf-8")
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(config, out_dir=config.root / "dist")
    assert (config.root / "dist" / "custom.txt").read_text(encoding="utf-8") == "custom"
    assert (config.root / "dist" / "images" / "a.txt").is_file()


def test_site_static_can_override_generated_assets(config) -> None:
    assets = config.static_dir / "assets"
    assets.mkdir(parents=True)
    (assets / "favicon.svg").write_text("<svg>custom</svg>", encoding="utf-8")
    (assets / "style.css").write_text("/* custom */", encoding="utf-8")
    write_post(config.root, "a.md", '---\ntitle: "A"\n---\nbody')
    build(config, out_dir=config.root / "dist")
    assert (config.root / "dist" / "assets" / "favicon.svg").read_text(encoding="utf-8") == "<svg>custom</svg>"
    assert (config.root / "dist" / "assets" / "style.css").read_text(encoding="utf-8") == "/* custom */"

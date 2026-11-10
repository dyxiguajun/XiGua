from __future__ import annotations

from xigua.rendering import post_process, pygments_css, render_markdown


def test_render_markdown_generates_toc_and_chinese_ids() -> None:
    html, toc = render_markdown("# 标题\n\n## 安装\n\n正文\n\n## 使用方式\n")
    assert 'id="安装"' in html
    assert 'id="使用方式"' in html
    assert 'href="#安装"' in toc
    assert "正文" in html


def test_render_markdown_highlights_code() -> None:
    html, _ = render_markdown("```python\nprint('hi')\n```\n")
    assert 'class="highlight"' in html
    assert "print" in html


def test_post_process_adds_external_link_attrs_once() -> None:
    html = post_process('<a href="https://example.com">x</a>')
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html

    again = post_process(html)
    assert again.count('target="_blank"') == 1


def test_post_process_respects_existing_link_target() -> None:
    html = post_process('<a href="https://example.com" target="_self">x</a>')
    assert 'target="_blank"' not in html


def test_post_process_handles_self_closing_images() -> None:
    html = post_process('<img src="x.png" />')
    assert html == '<img src="x.png" loading="lazy" decoding="async" />'


def test_post_process_does_not_duplicate_image_attrs() -> None:
    html = post_process('<img src="x.png" loading="eager" decoding="sync">')
    assert html.count("loading=") == 1
    assert html.count("decoding=") == 1


def test_pygments_css_is_scoped() -> None:
    css = pygments_css()
    assert ".highlight" in css
    assert "pre" in css

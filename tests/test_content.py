from __future__ import annotations

from datetime import date

import pytest

from tests.conftest import write_post
from xigua.content import load_posts, normalize_tags, parse_front_matter
from xigua.errors import ContentError


def test_parse_front_matter() -> None:
    meta, body = parse_front_matter(
        '---\ntitle: "你好"\ntags: [Python]\n---\n\n正文。\n'
    )
    assert meta == {"title": "你好", "tags": ["Python"]}
    assert body.strip() == "正文。"


def test_parse_front_matter_absent() -> None:
    meta, body = parse_front_matter("# 标题\n\n正文")
    assert meta == {}
    assert body == "# 标题\n\n正文"


def test_parse_front_matter_invalid_yaml() -> None:
    with pytest.raises(ContentError, match="YAML"):
        parse_front_matter("---\ntitle: [\n---\nbody")


def test_parse_front_matter_must_be_mapping() -> None:
    with pytest.raises(ContentError, match="键值表"):
        parse_front_matter("---\n- a\n- b\n---\nbody")


def test_normalize_tags() -> None:
    assert normalize_tags(None) == ()
    assert normalize_tags("Python, 笔记, #Python") == ("Python", "笔记")
    assert normalize_tags(["a", " b ", 3]) == ("a", "b", "3")
    with pytest.raises(ContentError):
        normalize_tags({"bad": True})


def test_loads_posts_and_derives_metadata(config) -> None:
    write_post(
        config.root,
        "2026-01-02-hello.md",
        """
        ---
        title: "Hello"
        tags: [Python, 测试]
        description: "摘要"
        ---

        # Hello

        正文内容。
        """,
    )
    write_post(
        config.root,
        "2026-02-03-second.md",
        """
        # 第二篇

        没有 front matter 的文章。
        """,
    )

    posts = load_posts(config)
    assert [post.title for post in posts] == ["第二篇", "Hello"]
    first, second = posts
    assert first.date == date(2026, 2, 3)
    assert first.slug == "第二篇"
    assert second.date == date(2026, 1, 2)
    assert second.slug == "hello"
    assert second.tags == ("Python", "测试")
    assert second.description == "摘要"
    assert second.excerpt == "摘要"
    assert second.path == "blog/hello/"
    assert second.reading_minutes >= 1
    assert "正文内容" in second.html


def test_drafts_are_hidden_by_default(config) -> None:
    write_post(
        config.root,
        "2026-01-01-draft.md",
        """
        ---
        title: "草稿"
        draft: true
        ---
        内容
        """,
    )
    assert load_posts(config) == []
    drafts = load_posts(config, include_drafts=True)
    assert len(drafts) == 1
    assert drafts[0].draft is True


def test_pinned_posts_come_first(config) -> None:
    write_post(
        config.root,
        "2026-01-01-a.md",
        '---\ntitle: "A"\ndate: 2026-01-01\n---\nA',
    )
    write_post(
        config.root,
        "2026-01-02-b.md",
        '---\ntitle: "B"\ndate: 2026-01-02\npinned: true\n---\nB',
    )
    assert [post.title for post in load_posts(config)] == ["B", "A"]


def test_duplicate_slugs_are_made_unique(config, caplog) -> None:
    for name in ("a.md", "b.md"):
        write_post(
            config.root,
            name,
            '---\ntitle: "Same"\ndate: 2026-01-01\n---\nContent',
        )
    posts = load_posts(config)
    assert len({post.slug for post in posts}) == 2
    assert "重复" in caplog.text


def test_invalid_date_raises(config) -> None:
    write_post(
        config.root,
        "bad.md",
        '---\ntitle: "Bad"\ndate: "not-a-date"\n---\nBody',
    )
    with pytest.raises(ContentError, match="日期"):
        load_posts(config)


def test_missing_posts_directory(config) -> None:
    config.posts_dir.rmdir()
    with pytest.raises(ContentError, match="文章目录"):
        load_posts(config)


def test_title_from_filename(config) -> None:
    write_post(config.root, "2026-05-06-my-first-post.md", "正文")
    post = load_posts(config)[0]
    assert post.title == "my first post"
    assert post.slug == "my-first-post"

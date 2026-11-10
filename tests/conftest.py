from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from xigua.config import load_config


@pytest.fixture()
def site(tmp_path: Path) -> Path:
    """Create a minimal valid site and return its root."""
    (tmp_path / "posts").mkdir()
    (tmp_path / "xigua.toml").write_text(
        textwrap.dedent(
            """
            [site]
            title = "测试站点"
            description = "一个测试站点"
            url = "https://example.com/base"
            lang = "zh-CN"
            author = "测试作者"

            [profile]
            status = "正在测试"
            headline = "测试工程师"
            bio = "简介"

            [[links]]
            label = "GitHub"
            url = "https://github.com/example"

            [[projects]]
            name = "示例项目"
            description = "它做了一些事情。"
            tags = ["Python", "测试"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def config(site: Path):
    return load_config(site)


def write_post(root: Path, name: str, text: str) -> Path:
    path = root / "posts" / name
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path

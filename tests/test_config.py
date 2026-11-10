from __future__ import annotations

from pathlib import Path

import pytest

from xigua.config import load_config
from xigua.errors import ConfigError


def test_loads_site_config(config) -> None:
    assert config.title == "测试站点"
    assert config.url == "https://example.com/base"
    assert config.lang == "zh-CN"
    assert config.author == "测试作者"
    assert config.profile.headline == "测试工程师"
    assert len(config.links) == 1
    assert config.links[0].label == "GitHub"
    assert len(config.projects) == 1
    assert config.projects[0].tags == ("Python", "测试")
    # The default navigation is localized and used when [[nav]] is absent.
    assert [item.label for item in config.nav] == ["首页", "文章", "标签"]
    assert config.posts_dir == config.root / "posts"
    assert config.out_dir == config.root / "dist"


def test_accepts_a_config_file_path(config) -> None:
    again = load_config(config.config_path)
    assert again.root == config.root


def test_rejects_missing_title(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text('[site]\ntitle = ""\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="site.title"):
        load_config(tmp_path)


def test_rejects_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text("[site\ntitle = 1", encoding="utf-8")
    with pytest.raises(ConfigError, match="TOML"):
        load_config(tmp_path)


def test_rejects_invalid_accent(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text(
        '[site]\ntitle = "x"\naccent = "orange"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="accent"):
        load_config(tmp_path)


def test_rejects_invalid_url(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text(
        '[site]\ntitle = "x"\nurl = "example.com"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="site.url"):
        load_config(tmp_path)


def test_rejects_incomplete_link(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text(
        '[site]\ntitle = "x"\n\n[[links]]\nlabel = "GitHub"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="label 和 url"):
        load_config(tmp_path)


def test_custom_nav_and_paths(tmp_path: Path) -> None:
    (tmp_path / "xigua.toml").write_text(
        """
[site]
title = "x"
lang = "en"

[[nav]]
label = "Home"
href = ""

[[nav]]
label = "Now"
href = "now/"

[content]
posts = "writing"
static = "public"

[build]
out = "_site"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert [item.href for item in config.nav] == ["", "now/"]
    assert config.posts_dir == tmp_path / "writing"
    assert config.static_dir == tmp_path / "public"
    assert config.out_dir == tmp_path / "_site"


def test_missing_config(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="xigua.toml"):
        load_config(tmp_path)


def test_wrong_config_file_name(tmp_path: Path) -> None:
    path = tmp_path / "other.toml"
    path.write_text('[site]\ntitle = "x"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="xigua.toml"):
        load_config(path)

"""Load and validate ``xigua.toml``."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigError
from .utils import is_hex_color

DEFAULT_ACCENT = "#ea580c"


@dataclass(frozen=True)
class NavItem:
    label: str
    href: str


@dataclass(frozen=True)
class Link:
    label: str
    url: str
    icon: str = ""


@dataclass(frozen=True)
class SiteProject:
    name: str
    description: str = ""
    url: str = ""
    tags: tuple[str, ...] = ()
    year: str = ""


@dataclass(frozen=True)
class Profile:
    status: str = ""
    headline: str = ""
    bio: str = ""
    location: str = ""
    avatar: str = ""


@dataclass(frozen=True)
class SiteConfig:
    root: Path
    config_path: Path
    title: str
    description: str = ""
    url: str = ""
    lang: str = "zh-CN"
    author: str = ""
    accent: str = DEFAULT_ACCENT
    footer: str = ""
    profile: Profile = field(default_factory=Profile)
    links: tuple[Link, ...] = ()
    projects: tuple[SiteProject, ...] = ()
    nav: tuple[NavItem, ...] = ()
    posts_dir: Path = Path("posts")
    static_dir: Path = Path("static")
    out_dir: Path = Path("dist")
    cname: str = ""


def _as_str(value: Any, field_name: str, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ConfigError(f"`{field_name}` 必须是字符串。")
    return value.strip()


def _as_tags(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple)):
        items = []
        for item in value:
            if not isinstance(item, (str, int, float)):
                raise ConfigError(f"`{field_name}` 里的标签必须是字符串。")
            items.append(str(item).strip())
    else:
        raise ConfigError(f"`{field_name}` 必须是字符串或字符串数组。")
    return tuple(item for item in items if item)


def _table(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError(f"`[{key}]` 必须是一个表（table）。")
    return value


def _array_of_tables(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ConfigError(f"`[[{key}]]` 必须是表数组。")
    return value


def _resolve_root(target: Path) -> tuple[Path, Path]:
    target = target.expanduser()
    if target.is_file():
        if target.name != "xigua.toml":
            raise ConfigError(f"配置文件必须叫 xigua.toml，而不是 {target.name}。")
        return target.resolve().parent, target.resolve()
    if target.is_dir():
        config_path = target / "xigua.toml"
        if not config_path.exists():
            raise ConfigError(f"在 {target} 下找不到 xigua.toml。先运行 `xigua init`。")
        return target.resolve(), config_path.resolve()
    raise ConfigError(f"路径不存在：{target}")


def _default_nav(lang: str) -> tuple[NavItem, ...]:
    if lang.lower().startswith("zh"):
        return (NavItem("首页", ""), NavItem("文章", "blog/"), NavItem("标签", "tags/"))
    return (NavItem("Home", ""), NavItem("Writing", "blog/"), NavItem("Tags", "tags/"))


def load_config(target: Path | str = ".") -> SiteConfig:
    """Read ``xigua.toml`` and return a validated configuration."""
    root, config_path = _resolve_root(Path(target))
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{config_path.name} 不是合法的 TOML：{exc}") from exc
    except OSError as exc:
        raise ConfigError(f"读取 {config_path} 失败：{exc}") from exc

    site = _table(data, "site")
    title = _as_str(site.get("title"), "site.title")
    if not title:
        raise ConfigError("`site.title` 不能为空。")

    lang = _as_str(site.get("lang"), "site.lang", "zh-CN") or "zh-CN"
    url = _as_str(site.get("url"), "site.url").rstrip("/")
    if url and not url.startswith(("http://", "https://")):
        raise ConfigError("`site.url` 必须以 http:// 或 https:// 开头。")

    accent = _as_str(site.get("accent"), "site.accent", DEFAULT_ACCENT) or DEFAULT_ACCENT
    if not is_hex_color(accent):
        raise ConfigError("`site.accent` 必须是十六进制颜色，例如 #ea580c。")

    profile_data = _table(data, "profile")
    profile = Profile(
        status=_as_str(profile_data.get("status"), "profile.status"),
        headline=_as_str(profile_data.get("headline"), "profile.headline"),
        bio=_as_str(profile_data.get("bio"), "profile.bio"),
        location=_as_str(profile_data.get("location"), "profile.location"),
        avatar=_as_str(profile_data.get("avatar"), "profile.avatar"),
    )

    links: list[Link] = []
    for index, item in enumerate(_array_of_tables(data, "links"), start=1):
        label = _as_str(item.get("label"), f"links[{index}].label")
        href = _as_str(item.get("url"), f"links[{index}].url")
        if not label or not href:
            raise ConfigError(f"第 {index} 个 [[links]] 需要同时填写 label 和 url。")
        if not href.startswith(("http://", "https://", "mailto:")):
            raise ConfigError(f"第 {index} 个 [[links]].url 必须是 http(s) 或 mailto 链接。")
        links.append(Link(label, href, _as_str(item.get("icon"), f"links[{index}].icon")))

    projects: list[SiteProject] = []
    for index, item in enumerate(_array_of_tables(data, "projects"), start=1):
        name = _as_str(item.get("name"), f"projects[{index}].name")
        if not name:
            raise ConfigError(f"第 {index} 个 [[projects]] 需要填写 name。")
        projects.append(
            SiteProject(
                name=name,
                description=_as_str(item.get("description"), f"projects[{index}].description"),
                url=_as_str(item.get("url"), f"projects[{index}].url"),
                tags=_as_tags(item.get("tags"), f"projects[{index}].tags"),
                year=_as_str(item.get("year"), f"projects[{index}].year"),
            )
        )

    nav: list[NavItem] = []
    for index, item in enumerate(_array_of_tables(data, "nav"), start=1):
        label = _as_str(item.get("label"), f"nav[{index}].label")
        href = _as_str(item.get("href"), f"nav[{index}].href")
        if not label:
            raise ConfigError(f"第 {index} 个 [[nav]] 需要填写 label。")
        nav.append(NavItem(label, href))

    content = _table(data, "content")
    build = _table(data, "build")
    posts_dir = root / (_as_str(content.get("posts"), "content.posts", "posts") or "posts")
    static_dir = root / (_as_str(content.get("static"), "content.static", "static") or "static")
    out_dir = root / (_as_str(build.get("out"), "build.out", "dist") or "dist")

    return SiteConfig(
        root=root,
        config_path=config_path,
        title=title,
        description=_as_str(site.get("description"), "site.description"),
        url=url,
        lang=lang,
        author=_as_str(site.get("author"), "site.author"),
        accent=accent,
        footer=_as_str(site.get("footer"), "site.footer"),
        profile=profile,
        links=tuple(links),
        projects=tuple(projects),
        nav=tuple(nav) or _default_nav(lang),
        posts_dir=posts_dir,
        static_dir=static_dir,
        out_dir=out_dir,
        cname=_as_str(site.get("cname"), "site.cname"),
    )

"""Command line interface for XiGua."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from . import __version__
from .build import build
from .config import load_config
from .content import load_posts, normalize_tags
from .errors import XiguaError
from .rendering import STATIC_DIR, TEMPLATE_DIR
from .server import serve
from .utils import human_date, slugify

SCAFFOLD_CONFIG = """\
[site]
title = "{title}"
description = "一句话介绍这个站点。"
url = ""
lang = "zh-CN"
author = "{title}"
accent = "#ea580c"
footer = ""

[profile]
status = "正在写代码"
headline = "在这里写一句你正在做的事"
bio = "你好，我是 {title}。这个站点由 XiGua 生成。"
location = ""
avatar = ""

# 取消注释，添加你的链接和项目：
# [[links]]
# label = "GitHub"
# url = "https://github.com/your-name"
#
# [[projects]]
# name = "一个项目"
# description = "它解决了什么问题。"
# url = "https://github.com/your-name/project"
# tags = ["Python"]
"""

SCAFFOLD_POST = """\
---
title: "你好，世界"
date: {date}
tags:
  - 开始
description: "这是这个站点的第一篇文章。"
draft: false
---

这是用 XiGua 生成的第一篇文章。

## 为什么写下来

写作是最好的思考方式。把正在做的事、踩过的坑、想明白的问题写下来，
它们会在未来某个时刻帮到别人，也帮到你自己。

## 下一步

- 修改 `xigua.toml` 里的个人信息
- 运行 `xigua new "文章标题"` 新建文章
- 运行 `xigua serve` 本地预览
"""


def _site_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--site",
        default=".",
        metavar="PATH",
        help="站点目录或 xigua.toml 路径（默认：当前目录）",
    )


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise XiguaError(f"{target} 不是目录。")

    config_path = target / "xigua.toml"
    if config_path.exists() and not args.force:
        raise XiguaError(f"{config_path} 已存在。加 --force 覆盖它。")

    title = args.title or target.name or "我的站点"
    target.mkdir(parents=True, exist_ok=True)
    (target / "posts").mkdir(exist_ok=True)

    config_path.write_text(SCAFFOLD_CONFIG.format(title=title), encoding="utf-8")
    welcome = target / "posts" / "welcome.md"
    if not welcome.exists() or args.force:
        welcome.write_text(SCAFFOLD_POST.format(date=date.today().isoformat()), encoding="utf-8")

    print(f"已创建站点：{target}")
    print(f"  {config_path.name}")
    print("  posts/welcome.md")
    print("\n下一步：")
    print(f"  cd {target}" if target != Path.cwd() else "  # 你已经在站点目录里")
    print("  xigua serve")
    return 0


def _parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise XiguaError(f"日期格式不对：{value}。请使用 YYYY-MM-DD。") from exc


def cmd_new(args: argparse.Namespace) -> int:
    config = load_config(args.site)
    title = args.title.strip()
    if not title:
        raise XiguaError("文章标题不能为空。")

    post_date = _parse_date(args.date)
    tags = normalize_tags(args.tags)
    slug = slugify(args.slug or title)
    config.posts_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{post_date.isoformat()}-{slug}"
    path = config.posts_dir / f"{base_name}.md"
    index = 2
    while path.exists():
        path = config.posts_dir / f"{base_name}-{index}.md"
        index += 1

    meta = {
        "title": title,
        "date": post_date.isoformat(),
        "tags": list(tags),
        "description": "",
        "draft": False,
    }
    front_matter = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    body = "在这里开始写作。\n\n## 一个小标题\n\n正文。\n"
    path.write_text(f"---\n{front_matter}\n---\n\n{body}", encoding="utf-8")

    print(f"已创建：{path}")
    print(f"标题：{title}")
    print(f"日期：{human_date(post_date, config.lang)}")
    print("\n下一步：")
    print(f"  编辑 {path.name}，然后运行 xigua serve")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    config = load_config(args.site)
    result = build(
        config,
        out_dir=Path(args.out) if args.out else None,
        base_url=args.base_url,
        include_drafts=args.drafts,
        clean=not args.no_clean,
    )
    print(f"完成：{result.posts} 篇文章 · {result.tags} 个标签 · {result.pages} 个页面")
    print(f"输出：{result.out_dir}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    config = load_config(args.site)
    out = Path(args.out).expanduser().resolve() if args.out else config.out_dir
    display_host = "localhost" if args.host in {"0.0.0.0", "::"} else args.host
    base_url = f"http://{display_host}:{args.port}"

    def rebuild() -> None:
        current = load_config(args.site)
        build(
            current,
            out_dir=out,
            base_url=base_url,
            include_drafts=args.drafts,
            clean=True,
        )

    rebuild()
    watch_paths = [config.config_path, config.posts_dir, config.static_dir, TEMPLATE_DIR, STATIC_DIR]
    serve(
        out,
        host=args.host,
        port=args.port,
        watch_paths=watch_paths if args.watch else (),
        rebuild=rebuild if args.watch else None,
    )
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(args.site)
    posts = load_posts(config, include_drafts=True)
    drafts = sum(1 for post in posts if post.draft)
    tags = sorted({tag for post in posts for tag in post.tags})

    print(f"站点：{config.title}")
    print(f"配置：{config.config_path}")
    print(f"文章：{len(posts)} 篇（其中草稿 {drafts} 篇）")
    print(f"标签：{'、'.join(tags) if tags else '暂无'}")
    print(f"输出：{config.out_dir}")

    warnings: list[str] = []
    if not config.url:
        warnings.append("没有设置 site.url，RSS/sitemap 会使用相对链接。")
    if not posts:
        warnings.append("posts/ 里还没有文章。")
    if not config.description:
        warnings.append("没有设置 site.description，搜索结果里会缺少摘要。")
    if config.profile.avatar and not config.profile.avatar.startswith(("http://", "https://")):
        warnings.append("profile.avatar 不是完整 URL，部署后可能找不到图片。")

    if warnings:
        print("\n提示：")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n一切正常。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xigua",
        description="把一份配置和 Markdown 变成个人主页 + 博客。",
    )
    parser.add_argument("--version", action="version", version=f"xigua {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="创建一个新站点")
    init.add_argument("path", nargs="?", default=".", help="目标目录（默认：当前目录）")
    init.add_argument("--title", help="站点标题（默认：目录名）")
    init.add_argument("--force", action="store_true", help="覆盖已有的 xigua.toml 和示例文章")
    init.set_defaults(func=cmd_init)

    new = sub.add_parser("new", help="新建一篇文章")
    new.add_argument("title", help="文章标题")
    _site_arg(new)
    new.add_argument("--date", help="日期，格式 YYYY-MM-DD（默认：今天）")
    new.add_argument("--tags", help="逗号分隔的标签，例如 Python,笔记")
    new.add_argument("--slug", help="自定义 URL 片段")
    new.set_defaults(func=cmd_new)

    build_cmd = sub.add_parser("build", help="生成静态站点")
    _site_arg(build_cmd)
    build_cmd.add_argument("--out", help="输出目录（默认：xigua.toml 里的 build.out 或 dist）")
    build_cmd.add_argument("--base-url", help="覆盖 site.url，例如 http://localhost:8000")
    build_cmd.add_argument("--drafts", action="store_true", help="连同草稿一起生成")
    build_cmd.add_argument("--no-clean", action="store_true", help="保留输出目录里已有的文件")
    build_cmd.set_defaults(func=cmd_build)

    serve_cmd = sub.add_parser("serve", help="本地预览，并在文件变化时重新生成")
    _site_arg(serve_cmd)
    serve_cmd.add_argument("--out", help="输出目录")
    serve_cmd.add_argument("--host", default="127.0.0.1", help="监听地址（默认：127.0.0.1）")
    serve_cmd.add_argument("--port", type=int, default=8000, help="端口（默认：8000）")
    serve_cmd.add_argument("--drafts", action="store_true", help="预览草稿")
    serve_cmd.add_argument("--no-watch", dest="watch", action="store_false", help="关闭文件监听")
    serve_cmd.set_defaults(func=cmd_serve, watch=True)

    check = sub.add_parser("check", help="检查配置和文章")
    _site_arg(check)
    check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except XiguaError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""generate_blog.py
将 posts/*.md 转换为静态博客页面（HTML）。
依赖：pip install markdown
"""
from __future__ import annotations
import datetime
import os
import pathlib
import re
import sys
import logging
import html

# module logger
logger = logging.getLogger(__name__)

try:
    import markdown
except Exception:
    # Do not exit during import — provide a tiny fallback so tests and other imports don't fail.
    # The real Markdown features require the 'markdown' package; prompt users at runtime when build() is called.
    def _markdown_fallback(md_text, extensions=None):
        # Minimal conversion: preserve lines and escape less-than signs.
        return '<p>' + md_text.replace('&', '&amp;').replace('<', '&lt;').replace('\n', '<br>') + '</p>'

    import types
    markdown = types.SimpleNamespace(markdown=_markdown_fallback)
    _MISSING_MARKDOWN = True
else:
    _MISSING_MARKDOWN = False

ROOT = pathlib.Path(__file__).resolve().parent
POSTS_DIR = ROOT / "posts"
OUT_DIR = ROOT / "blog"
TEMPLATE_PATH = ROOT / "blog" / "template.html"
BILIBILI = "https://space.bilibili.com/402631059?spm_id_from=333.1007.0.0"

# improved slugify: normalize unicode, remove unwanted chars
slugify_re = re.compile(r"[^a-z0-9-]+")

import unicodedata

def slugify(s: str) -> str:
    s = unicodedata.normalize('NFKD', s)
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = s.lower().strip().replace(' ', '-')
    return slugify_re.sub('', s)


def parse_post(md_text: str, filename: str) -> dict:
    # 标题：首个 H1 (# )，否则使用文件名
    lines = md_text.splitlines()
    title = None
    for ln in lines:
        if ln.startswith('# '):
            title = ln[2:].strip()
            break
    if not title:
        title = pathlib.Path(filename).stem

    # 尝试从文件名中解析日期 YYYY-MM-DD
    date = None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", pathlib.Path(filename).stem)
    if m:
        date = m.group(1)
    else:
        date = datetime.date.today().isoformat()

    html_content = markdown.markdown(md_text, extensions=["fenced_code", "codehilite"])
    return {"title": title, "date": date, "content": html_content}


def build(out_dir: pathlib.Path = OUT_DIR, posts_dir: pathlib.Path = POSTS_DIR, template_path: pathlib.Path = TEMPLATE_PATH) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    if not posts_dir.exists():
        raise FileNotFoundError(f"posts directory not found: {posts_dir}")

    template = template_path.read_text(encoding='utf-8')

    today = datetime.date.today()
    if _MISSING_MARKDOWN:
        logger.warning("Markdown package not installed; using a simple fallback for rendering. For better results install: pip install markdown")

    posts = []
    for p in sorted(posts_dir.glob('*.md'), reverse=True):
        md_text = p.read_text(encoding='utf-8')
        meta = parse_post(md_text, p.name)
        slug = slugify(meta['title']) or p.stem
        out_file = out_dir / f"{slug}.html"
        html_page = template.format(title=html.escape(meta['title']), date=meta['date'], content=meta['content'], year=today.year, bilibili=BILIBILI)
        out_file.write_text(html_page, encoding='utf-8')
        posts.append({"title": meta['title'], "date": meta['date'], "slug": slug})

    # 生成索引页
    if posts:
        index_items = [f"<li><a href='{post['slug']}.html'>{html.escape(post['title'])}</a> <small>({post['date']})</small></li>" for post in sorted(posts, key=lambda x: x['date'], reverse=True)]
        index_html = "\n".join(index_items)
    else:
        index_html = "<p>暂无文章，敬请期待。</p>"
    index_page = """<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1'>
  <title>博客</title>
  <link rel='stylesheet' href='https://unpkg.com/@picocss/pico@latest/css/pico.min.css'>
</head>
<body>
  <main style='max-width:900px;margin:32px auto;padding:0 16px;'>
    <h1>博客</h1>
    <p class='muted'>最新文章</p>
    <ul>
      {items}
    </ul>
    <hr>
    <p><a href='../index.html'>返回简介</a></p>
  </main>
</body>
</html>""".format(items=index_html)
    (out_dir / 'index.html').write_text(index_page, encoding='utf-8')

    logger.info("生成完成：%d 篇文章 -> %s", len(posts), out_dir)
    print(f"生成完成：{len(posts)} 篇文章 -> {out_dir}")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description='生成静态博客页面')
    p.add_argument('--posts', default=str(POSTS_DIR), help='posts 目录')
    p.add_argument('--out', default=str(OUT_DIR), help='输出目录')
    p.add_argument('--template', default=str(TEMPLATE_PATH), help='模板文件路径')
    args = p.parse_args(argv)

    build(out_dir=pathlib.Path(args.out), posts_dir=pathlib.Path(args.posts), template_path=pathlib.Path(args.template))


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""generate_intro.py
生成个人简介的 Markdown 与 HTML 文件。
默认信息基于：俄勒冈州立大学留学生、全栈开发者、主要使用 Python、3 年开发经验、物联网经验、正在学习 HarmonyOS、Bilibili 主页。
"""

from __future__ import annotations
import argparse
import datetime
import html
import textwrap
import typing
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

DEFAULT = {
    "school": "俄勒冈州立大学（Oregon State University）",
    "status": "留学生",
    "role": "全栈开发者 & 在校学生",
    "language": "Python",
    "years": "3 年",
    "iot": True,
    "learning": "HarmonyOS",
    "bilibili": "https://space.bilibili.com/402631059?spm_id_from=333.1007.0.0",
}

MD_TEMPLATE_CN = textwrap.dedent("""
## 自我介绍

**身份**
- {status} · {school}
- {role}

---

**技能与经验**
- 主要开发语言：**{language}**
- 开发经验：**{years}**
- 领域经验：**{iot_text}**
- 正在学习：**{learning}**

---

**个人主页 / 作品集**
> Bilibili: {bilibili}

---

**一句话介绍**
擅长把前端、后端与嵌入式设备结合，热衷于用 **Python** 快速实现从原型到产品的落地.
""")

MD_TEMPLATE_EN = textwrap.dedent("""
## About

**Identity**
- {status} · {school}
- {role}

---

**Skills & Experience**
- Main language: **{language}**
- Experience: **{years}**
- IoT experience: **{iot_text}**
- Currently learning: **{learning}**

---

**Portfolio**
> Bilibili: {bilibili}

---

**One-line bio**
Skilled at combining front-end, back-end, and embedded devices. I use **Python** to rapidly turn prototypes into production-ready projects.
""")

MD_TEMPLATE_FOOTER = textwrap.dedent(
    "> 最后更新：{date}\n> Last updated: {date}\n"
)

STYLE = textwrap.dedent("""
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; max-width: 720px; margin: 40px auto; line-height: 1.6; color: #222 }}
    h1,h2 {{ color: #111 }}
    a.button {{ display:inline-block; padding:8px 12px; background:#00a1d6; color:#fff; border-radius:6px; text-decoration:none }}
    blockquote {{ border-left:4px solid #eee; padding-left:12px; color:#555 }}
    .meta {{ color:#666; font-size:0.95em }}
  </style>
""")


HTML_TEMPLATE_CN = textwrap.dedent("""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>自我介绍</title>
  {style}
</head>
<body>
  <p><a href="blog/index.html">博客</a></p>
  <h2>自我介绍</h2>
  <p class="meta"><strong>{status}</strong> · {school}</p>
  <p><strong>{role}</strong></p>
  <hr>
  <h3>技能与经验</h3>
  <ul>
    <li>主要开发语言：<strong>{language}</strong></li>
    <li>开发经验：<strong>{years}</strong></li>
    <li>领域经验：<strong>{iot_text}</strong></li>
    <li>正在学习：<strong>{learning}</strong></li>
  </ul>
  <h3>个人主页 / 作品集</h3>
  <p><a class="button" href="{bilibili}" target="_blank" rel="noopener noreferrer">Bilibili 主页</a></p>
  <hr>
  <h3>一句话介绍</h3>
  <p>擅长把前端、后端与嵌入式设备结合，热衷于用 <strong>Python</strong> 快速实现从原型到产品的落地。</p>
  <footer><p class="meta">最后更新：{date}</p></footer>
</body>
</html>
""")

HTML_TEMPLATE_EN = textwrap.dedent("""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>About</title>
  {style}
</head>
<body>
  <p><a href="blog/index.html">Blog</a></p>
  <h2>About</h2>
  <p class="meta"><strong>{status}</strong> · {school}</p>
  <p><strong>{role}</strong></p>
  <hr>
  <h3>Skills & Experience</h3>
  <ul>
    <li>Main language: <strong>{language}</strong></li>
    <li>Experience: <strong>{years}</strong></li>
    <li>IoT experience: <strong>{iot_text}</strong></li>
    <li>Currently learning: <strong>{learning}</strong></li>
  </ul>
  <h3>Portfolio</h3>
  <p><a class="button" href="{bilibili}" target="_blank">Bilibili</a></p>
  <hr>
  <h3>One-line bio</h3>
  <p>Skilled at combining front-end, back-end, and embedded devices. I use <strong>Python</strong> to rapidly turn prototypes into production-ready projects.</p>
  <footer><p class="meta">Last updated: {date}</p></footer>
</body>
</html>
""")


def render_markdown(context: dict) -> str:
    """Render the markdown text from context according to language selection."""
    ctx = context.copy()
    ctx["date"] = datetime.date.today().isoformat()
    lang = ctx.get("lang", "both")

    parts = []
    # Generate language-specific IoT text to avoid mixing languages
    if lang in ("zh", "both"):
        ctx_zh = ctx.copy()
        ctx_zh["iot_text"] = "有物联网（IoT）项目经验" if ctx.get("iot") else "暂无物联网经验"
        parts.append(MD_TEMPLATE_CN.format(**ctx_zh))
    if lang in ("en", "both"):
        ctx_en = ctx.copy()
        ctx_en["iot_text"] = "Has IoT (IoT) project experience" if ctx.get("iot") else "No IoT experience"
        parts.append(MD_TEMPLATE_EN.format(**ctx_en))

    parts.append(MD_TEMPLATE_FOOTER.format(**ctx))
    return "\n\n".join(parts)


def write_text_file(path: typing.Union[str, Path], content: str) -> None:
    path = Path(path)
    # Ensure parent directories exist
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    logger.info("Wrote %s", path)


def render_html(context: dict) -> str:
    ctx = context.copy()
    ctx["iot_text"] = "有物联网（IoT）项目经验" if ctx.get("iot") else "暂无物联网经验"
    ctx["date"] = datetime.date.today().isoformat()
    # escape URL and simple fields
    ctx = {k: html.escape(str(v)) for k, v in ctx.items()}

    lang = ctx.get("lang", "both")
    if lang == "zh":
        html_str = HTML_TEMPLATE_CN.format(style=STYLE, **ctx)
    elif lang == "en":
        html_str = HTML_TEMPLATE_EN.format(style=STYLE, **ctx)
    else:
        html_str = HTML_TEMPLATE_BOTH.format(style=STYLE, **ctx)

    # Ensure target="_blank" links are safe by adding rel unless already present
    html_str = re.sub(r'target="_blank"(?![^>]*rel=)', 'target="_blank" rel="noopener noreferrer"', html_str)
    return html_str


HTML_TEMPLATE_BOTH = textwrap.dedent("""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>自我介绍 / About</title>
  {style}
</head>
<body>
  <!-- Chinese -->
  <h2>自我介绍</h2>
  <p class="meta"><strong>{status}</strong> · {school}</p>
  <p><strong>{role}</strong></p>
  <hr>
  <h3>技能与经验</h3>
  <ul>
    <li>主要开发语言：<strong>{language}</strong></li>
    <li>开发经验：<strong>{years}</strong></li>
    <li>领域经验：<strong>{iot_text}</strong></li>
    <li>正在学习：<strong>{learning}</strong></li>
  </ul>
  <h3>个人主页 / 作品集</h3>
  <p><a class="button" href="{bilibili}" target="_blank" rel="noopener noreferrer">Bilibili 主页</a></p>
  <hr>
  <h3>一句话介绍</h3>
  <p>擅长把前端、后端与嵌入式设备结合，热衷于用 <strong>Python</strong> 快速实现从原型到产品的落地。</p>

  <hr>

  <!-- English -->
  <h2>About</h2>
  <p class="meta"><strong>{status}</strong> · {school}</p>
  <p><strong>{role}</strong></p>
  <hr>
  <h3>Skills & Experience</h3>
  <ul>
    <li>Main language: <strong>{language}</strong></li>
    <li>Experience: <strong>{years}</strong></li>
    <li>IoT experience: <strong>{iot_text}</strong></li>
    <li>Currently learning: <strong>{learning}</strong></li>
  </ul>
  <h3>Portfolio</h3>
  <p><a class="button" href="{bilibili}" target="_blank">Bilibili</a></p>
  <hr>
  <h3>One-line bio</h3>
  <p>Skilled at combining front-end, back-end, and embedded devices. I use <strong>Python</strong> to rapidly turn prototypes into production-ready projects.</p>
  <footer><p class="meta">Last updated: {date} / 最后更新：{date}</p></footer>
</body>
</html>
""")

PREVIEW_TEMPLATE = textwrap.dedent("""
**介绍（预览）**  
{status} · {school} · {role}  
主要使用 {language}，有 {years} 开发经验，{iot_text}，正在学习 {learning}。  
Bilibili: {bilibili}  

**English (Preview)**  
{status} · {school} · {role}  
Main language: {language}, {years} experience, {iot_text}, currently learning {learning}.  
Bilibili: {bilibili}  
> 最后更新：{date}
""")


def render_preview(context: dict) -> str:
    ctx = context.copy()
    ctx["iot_text"] = "具有物联网（IoT）项目经验" if ctx.get("iot") else "暂无物联网经验"
    ctx["date"] = datetime.date.today().isoformat()
    lang = ctx.get('lang', 'both')

    if lang == 'zh':
        return textwrap.dedent("""
**介绍（预览）**  
{status} · {school} · {role}  
主要使用 {language}，有 {years} 开发经验，{iot_text}，正在学习 {learning}。  
Bilibili: {bilibili}  
> 最后更新：{date}
""").format(**ctx)
    elif lang == 'en':
        return textwrap.dedent("""
**English (Preview)**  
{status} · {school} · {role}  
Main language: {language}, {years} experience, {iot_text}, currently learning {learning}.  
Bilibili: {bilibili}  
> Last updated: {date}
""").format(**ctx)
    else:
        return PREVIEW_TEMPLATE.format(**ctx)


def main():
    p = argparse.ArgumentParser(description="生成个人简介的 Markdown、HTML 与预览文件")
    p.add_argument("--school", default=DEFAULT["school"], help="学校")
    p.add_argument("--status", default=DEFAULT["status"], help="身份")
    p.add_argument("--role", default=DEFAULT["role"], help="角色")
    p.add_argument("--language", default=DEFAULT["language"], help="主要开发语言")
    p.add_argument("--years", default=DEFAULT["years"], help="开发经验年限")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--iot", dest="iot", action="store_true", help="是否有物联网经验")
    group.add_argument("--no-iot", dest="iot", action="store_false", help="没有物联网经验")
    p.set_defaults(iot=DEFAULT["iot"])
    p.add_argument("--learning", default=DEFAULT["learning"], help="正在学习的技术")
    p.add_argument("--bilibili", default=DEFAULT["bilibili"], help="Bilibili 链接")
    p.add_argument("--out-md", default="INTRO.md", help="输出 Markdown 文件名")
    p.add_argument("--out-html", default="index.html", help="输出 HTML 文件名")
    p.add_argument("--out-preview", default="", help="输出预览 Markdown 文件名（为空则不输出）")
    p.add_argument("--lang", choices=["zh", "en", "both"], default="zh", help="输出语言：zh|en|both（默认：zh）")
    args = p.parse_args()

    ctx = vars(args)

    md = render_markdown(ctx)
    html_text = render_html(ctx)
    preview_text = render_preview(ctx) if args.out_preview else None

    write_text_file(args.out_md, md)
    write_text_file(args.out_html, html_text)

    if preview_text:
        write_text_file(args.out_preview, preview_text)

    msg = f"生成完成：{args.out_md}, {args.out_html}"
    if args.out_preview:
        msg += f", {args.out_preview}"
    logger.info(msg)


if __name__ == '__main__':
    main()

# XiGua（西瓜）

一个用 Python 写的小型静态站点生成器：一份 `xigua.toml` 加几个 Markdown 文件，就能生成个人主页、博客、标签页、RSS 和 sitemap。

没有数据库，没有前端构建，没有 Node.js。生成出来就是普通的 HTML / CSS / JS，可以放到任何静态托管上。

> 更完整的字段说明、模板结构和常见问题见 [docs/README.md](docs/README.md)。

## 它解决什么问题

这个仓库最早是两个各写各的脚本：一个把写死的个人信息拼成简介，另一个把 `posts/*.md` 转成博客页面。内容、模板和逻辑混在一起，换一个人用就要改源码。

现在它是一个完整的小工具：

- 个人信息、链接、项目、导航都写在 `xigua.toml` 里；
- 文章是带 front matter 的 Markdown；
- 一条命令生成整站，另一条命令本地预览；
- 模板、样式和脚本打包在 Python 包里，升级工具不会覆盖你的内容。

## 功能

- 首页：头像、状态、简介、社交链接、项目卡片、最近文章
- 博客：文章列表、标签云、浏览器内即时搜索（按 `/` 聚焦）
- 文章页：目录、阅读时间、上一篇 / 下一篇、相关文章、代码高亮、复制按钮
- 标签页：全部标签 + 每个标签的归档
- 自动生成 `feed.xml`、`sitemap.xml`、`robots.txt`、`search-index.json`、`404.html`
- 深浅色主题切换，跟随系统偏好，选择保存在浏览器里
- 阅读进度条、跳转到正文、语义化 HTML、Open Graph / Twitter / JSON-LD
- 响应式布局，打印样式，支持自定义主题色
- 草稿（`draft: true`）默认不发布
- 中文标题会保留可读的 URL，也可以手动指定 `slug`

## 快速开始

需要 **Python 3.11+**。

```bash
git clone https://github.com/dyxiguajun/XiGua.git
cd XiGua

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

新建一个站点：

```bash
xigua init my-site --title "我的站点"
cd my-site
xigua serve
```

打开 <http://localhost:8000> 预览。修改配置或文章后会自动重新生成，刷新浏览器即可。

也可以直接在当前仓库里预览已经配置好的站点：

```bash
xigua serve
xigua build
```

## 写文章

```bash
xigua new "我的第一篇文章" --tags Python,笔记
```

会在 `posts/` 下生成：

```markdown
---
title: 我的第一篇文章
date: 2026-02-14
tags:
  - Python
  - 笔记
description: ''
draft: false
---

在这里开始写作。

## 一个小标题

正文。
```

所有 front matter 字段都是可选的：

| 字段 | 说明 |
| --- | --- |
| `title` | 标题。省略时用正文的一级标题，再省略时用文件名 |
| `date` | 日期，推荐 `YYYY-MM-DD`。省略时用文件名开头的日期，再省略时用文件修改时间 |
| `tags` | 字符串或数组，例如 `[Python, 笔记]` |
| `description` | 摘要，用于列表、RSS 和搜索 |
| `draft` | `true` 时默认不参与构建 |
| `pinned` | `true` 时在列表中置顶 |
| `slug` | 自定义 URL 片段，默认由标题生成 |
| `cover` | 封面图 URL，显示在文章顶部 |

## 配置

站点的所有个性化内容都在 `xigua.toml`：

```toml
[site]
title = "西瓜"
description = "一句话介绍这个站点。"
url = "https://example.com"
lang = "zh-CN"
author = "西瓜"
accent = "#ea580c"
footer = "用 XiGua 生成 · 内容归作者所有"

[profile]
status = "在俄勒冈州立大学读计算机科学"
headline = "Python / Flutter / Arduino"
bio = "用 Python、Flutter 和 Arduino 做小项目，也在尝试各种 AI 开发工具。"
location = "Oregon, USA"
avatar = ""

[[links]]
label = "GitHub"
url = "https://github.com/your-name"

[[projects]]
name = "一个项目"
description = "它解决了什么问题。"
url = "https://github.com/your-name/project"
tags = ["Python"]
year = "2026"

[content]
posts = "posts"
static = "static"

[build]
out = "dist"
```

- `site.url` 用于 canonical、RSS、sitemap 和分享卡片。部署到 GitHub Pages 项目页时，填 `https://<用户名>.github.io/<仓库名>`。
- `site.accent` 支持 `#rgb` / `#rrggbb` 等十六进制颜色。
- `[[nav]]` 可以覆盖默认导航，`href` 使用相对站点根目录的路径，首页留空字符串。
- `[content]` 和 `[build]` 一般不需要改。

## 命令

| 命令 | 作用 |
| --- | --- |
| `xigua init [目录]` | 创建新站点（`--title`、`--force`） |
| `xigua new "标题"` | 新建文章（`--date`、`--tags`、`--slug`） |
| `xigua build` | 生成静态站点（`--out`、`--base-url`、`--drafts`、`--no-clean`） |
| `xigua serve` | 本地预览并监听文件变化（`--port`、`--host`、`--drafts`、`--no-watch`） |
| `xigua check` | 检查配置、文章数量和常见问题 |

`xigua new`、`build`、`serve`、`check` 都支持 `--site PATH`，用于在别的目录操作某个站点。

## 目录结构

```text
.
├── xigua.toml            # 站点配置
├── posts/                # Markdown 文章
├── static/               # 可选的额外静态文件，会原样复制到输出目录
├── dist/                 # 构建结果（已加入 .gitignore）
├── xigua/                # Python 包
│   ├── templates/        # Jinja 模板
│   ├── static/           # 内置样式和脚本
│   ├── build.py          # 构建流程
│   ├── content.py        # 文章解析
│   └── cli.py            # 命令行入口
└── tests/
```

需要放图片时，可以把文件放进 `static/`，然后在文章里写 `![说明](/images/example.jpg)`。

## 部署到 GitHub Pages

仓库里的 `.github/workflows/pages.yml` 已经配置好：推送到 `main` 后自动运行 `xigua build`，并把 `dist/` 发布到 GitHub Pages。

首次使用时，在仓库的 **Settings → Pages → Build and deployment** 里把 Source 选为 **GitHub Actions**。

如果部署在自定义域名或根路径，记得修改 `xigua.toml` 里的 `site.url`；项目页还要确保路径与 `<用户名>.github.io/<仓库名>` 一致。

其他静态托管（Cloudflare Pages、Netlify、Vercel）只需要：

- 构建命令：`pip install . && xigua build`
- 输出目录：`dist`

## 开发

```bash
pip install -e ".[dev]"
pytest
```

测试覆盖配置解析、front matter、日期与阅读时间、slug 去重、构建产物、RSS / sitemap、草稿过滤、CLI 等。

## 说明

这个项目是从早期两个一次性脚本重写而来，保留的核心想法是「用 Markdown 维护个人主页和博客」，其余部分重新设计。名字里的「西瓜」只是作者的昵称。

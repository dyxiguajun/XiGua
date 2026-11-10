# XiGua 使用手册

这份文档补充 README 里没有展开的细节：配置字段、构建行为、模板结构和常见问题。

## 安装

```bash
git clone https://github.com/dyxiguajun/XiGua.git
cd XiGua
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

只使用工具而不跑测试时，`pip install -e .` 就够了。

## 一次完整的初始化

```bash
xigua init blog --title "我的站点"
cd blog
xigua serve
```

`init` 会创建：

```text
blog/
├── xigua.toml
└── posts/
    └── welcome.md
```

想覆盖已有的同名文件：

```bash
xigua init blog --title "我的站点" --force
```

## `xigua.toml` 字段

### `[site]`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `title` | 字符串 | 必填 | 站点标题，也用于页头、页脚和 RSS |
| `description` | 字符串 | `""` | 站点描述 |
| `url` | 字符串 | `""` | 完整站点地址，例如 `https://example.com`；为空时生成相对链接 |
| `lang` | 字符串 | `zh-CN` | `<html lang>` 和日期格式 |
| `author` | 字符串 | `""` | 作者名，用于版权和 JSON-LD |
| `accent` | 字符串 | `#ea580c` | 主题色，十六进制 |
| `footer` | 字符串 | `""` | 页脚说明文字 |
| `cname` | 字符串 | `""` | 设置后会在输出目录生成 `CNAME` 文件 |

### `[profile]`

| 字段 | 说明 |
| --- | --- |
| `status` | 名字上方的小状态，例如「正在写代码」 |
| `headline` | 一句话身份 |
| `bio` | 简介，支持换行 |
| `location` | 地点 |
| `avatar` | 头像 URL；留空时显示站点标题首字 |

### `[[links]]`

```toml
[[links]]
label = "GitHub"
url = "https://github.com/your-name"
icon = "github"   # 可选，目前只作为元数据保留
```

`url` 必须以 `http://`、`https://` 或 `mailto:` 开头。

### `[[projects]]`

```toml
[[projects]]
name = "项目名"
description = "一句话说明。"
url = "https://example.com"
tags = ["Python", "Flutter"]
year = "2026"
```

只有 `name` 是必填的。有 `url` 时项目名会变成链接。

### `[[nav]]`

不写时根据语言生成默认导航：

- 中文：首页 / 文章 / 标签
- 其他：Home / Writing / Tags

自定义示例：

```toml
[[nav]]
label = "首页"
href = ""

[[nav]]
label = "文章"
href = "blog/"

[[nav]]
label = "关于"
href = "about/"
```

`href` 相对于站点根目录。`about/` 需要你自己在 `static/about/index.html` 里放页面。

### `[content]` 和 `[build]`

```toml
[content]
posts = "posts"   # 文章目录
static = "static" # 额外静态资源目录

[build]
out = "dist"      # 输出目录
```

路径相对于 `xigua.toml` 所在目录。

## 文章格式

```markdown
---
title: "标题"
date: 2026-02-14
tags:
  - Python
  - 笔记
description: "摘要"
draft: false
pinned: false
slug: "custom-slug"
cover: "https://example.com/cover.jpg"
---

正文。
```

### 标题推断顺序

1. front matter 的 `title`
2. 正文里的第一个 `# 标题`
3. 文件名去掉日期前缀后的部分

### 日期推断顺序

1. front matter 的 `date`
2. 文件名开头的 `YYYY-MM-DD`
3. 文件修改时间

### URL

默认由标题生成。中文会原样保留，空格和标点变成连字符：

```text
我的第一篇文章  ->  blog/我的第一篇文章/
Hello World     ->  blog/hello-world/
```

同一个 slug 出现多次时，后面的文章会变成 `slug-2`、`slug-3`，并在终端给出警告。

### 草稿与置顶

- `draft: true`：`xigua build` 默认跳过；`--drafts` 或 `xigua serve --drafts` 可以看到。
- `pinned: true`：在首页和文章列表中排在前面，置顶文章之间仍按日期排序。

## 输出内容

每次构建默认会清空输出目录，然后写入：

```text
dist/
├── index.html
├── 404.html
├── feed.xml
├── sitemap.xml
├── robots.txt
├── search-index.json
├── CNAME                # 仅配置了 site.cname 时
├── .nojekyll
├── assets/
│   ├── style.css
│   ├── app.js
│   ├── pygments.css
│   └── favicon.svg
├── blog/
│   ├── index.html
│   └── <slug>/index.html
└── tags/
    ├── index.html
    └── <tag>/index.html
```

`static/` 里的内容会复制到输出目录根部。例如 `static/images/a.png` 会变成 `dist/images/a.png`。

不想清空输出目录时：

```bash
xigua build --no-clean
```

## 本地预览

```bash
xigua serve
xigua serve --port 9000
xigua serve --drafts
xigua serve --no-watch
```

预览服务器会：

- 对 `/blog/` 这类路径返回对应的 `index.html`；
- 找不到页面时返回自定义 `404.html`；
- 监听配置、文章、模板和内置静态文件，改动后自动重新构建。

`serve` 会把 `site.url` 覆盖成 `http://localhost:<端口>`，避免本地预览时 canonical 指向线上地址。

## 构建时覆盖站点地址

```bash
xigua build --base-url https://preview.example.com
```

适合预览环境或临时部署到子路径。

## 自定义样式

优先使用 `static/` 覆盖，而不是改包内文件：

```text
static/
└── assets/
    └── style.css
```

构建时会先复制包内资源，再复制 `static/`，所以同名文件会被你的版本覆盖。升级 XiGua 时不会丢失。

主题色最简单的改法是 `xigua.toml` 里的 `site.accent`。它会被注入为 CSS 变量 `--accent`，影响链接、按钮、进度条和 favicon。

## 模板

模板在 `xigua/templates/`：

| 文件 | 页面 |
| --- | --- |
| `base.html` | 所有页面共享的 head、页头、页脚 |
| `index.html` | 首页 |
| `blog.html` | 文章列表 |
| `post.html` | 文章详情 |
| `tags.html` | 全部标签 |
| `tag.html` | 单个标签 |
| `404.html` | 404 页面 |

模板里可以使用：

- `site`：解析后的站点配置
- `url_for(path)`：根据当前页面深度生成相对链接
- `abs(path)`：生成绝对链接
- `datefmt` 过滤器：按 `site.lang` 格式化日期
- `tag_slug` 过滤器：把标签转成 URL 片段

## 常见问题

### 中文 URL 在 RSS 里变成了 `%E4%B8%AD...`

这是正常的 URL 编码，浏览器和阅读器会正确解码。

### 部署后样式或链接 404

检查 `site.url` 是否和实际部署地址一致。GitHub Pages 项目页应写成：

```toml
url = "https://<用户名>.github.io/<仓库名>"
```

### 修改文章后页面没变化

`xigua serve` 默认监听文件变化。如果用了 `--no-watch`，需要重新运行 `xigua build`，或刷新前手动构建。

### 构建提示 slug 重复

两篇文章标题相同。给其中一篇加 `slug`：

```yaml
slug: "another-post"
```

### 想删除示例文章

直接删除 `posts/welcome.md` 或 `posts/` 里不需要的 Markdown 文件，再构建。

## 开发与测试

```bash
pip install -e ".[dev]"
pytest
pytest --cov=xigua
```

测试使用临时目录，不会修改仓库里的 `dist/`。

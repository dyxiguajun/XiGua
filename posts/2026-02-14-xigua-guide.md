---
title: "用 XiGua 搭一个自己的主页和博客"
date: 2026-02-14
tags:
  - Python
  - 工具
  - 教程
description: "从零开始，用一份 TOML 配置和 Markdown 文件生成可以部署的个人站点。"
draft: false
---

这个站点本身由 **XiGua** 生成。它的目标很简单：不引入数据库、不依赖前端框架，只要会写 Markdown，就能维护一个干净的个人主页和博客。

## 安装

需要 Python 3.11 或更高版本。

```bash
git clone https://github.com/dyxiguajun/XiGua.git
cd XiGua
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows 的激活命令是：

```powershell
.venv\Scripts\activate
```

## 初始化站点

在一个空目录里运行：

```bash
xigua init my-site --title "我的站点"
cd my-site
xigua serve
```

浏览器打开 `http://localhost:8000`，就能看到本地预览。修改 `xigua.toml` 或 `posts/` 里的 Markdown，页面会自动重新生成。

## 写一篇文章

```bash
xigua new "第一篇正式文章" --tags Python,笔记
```

命令会在 `posts/` 下创建带 front matter 的 Markdown 文件：

```markdown
---
title: "第一篇正式文章"
date: 2026-02-14
tags:
  - Python
  - 笔记
description: ""
draft: false
---

在这里开始写作。
```

`title` 和 `date` 都可以省略：XiGua 会从正文的一级标题和文件名里的日期推断。`draft: true` 的文章默认不会出现在构建结果里。

## 构建

```bash
xigua build
```

输出在 `dist/`，包含：

- 首页、文章列表、文章页、标签页
- `feed.xml`、`sitemap.xml`、`robots.txt`
- 搜索索引 `search-index.json`
- 自动生成的 favicon 和语法高亮样式

部署时，把 `dist/` 交给 GitHub Pages、Cloudflare Pages 或任意静态托管即可。

## 配置站点

大部分个性化内容都在 `xigua.toml`：

```toml
[site]
title = "西瓜"
description = "一句话介绍"
url = "https://example.com"
lang = "zh-CN"
author = "西瓜"
accent = "#ea580c"

[profile]
status = "正在写代码"
headline = "计算机科学学生"
bio = "介绍一下自己"

[[links]]
label = "GitHub"
url = "https://github.com/your-name"
```

`accent` 支持十六进制颜色，会同时影响按钮、链接、进度条和 favicon。

## 最后

工具应该帮你把注意力放回内容上。如果你只想记录，不想维护一套复杂的前端工程，XiGua 大概就是为这个场景准备的。

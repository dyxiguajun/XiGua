# XiGua — 个人简介与博客生成工具

[![CI](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml) [![Pages](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml)

项目站点（部署到 GitHub Pages）: https://dyxiguajun.github.io/XiGua/

一个小型静态内容生成仓库，用于：
- 根据个人信息生成 Markdown 与 HTML 格式的自我介绍（`generate_intro.py`）。
- 将 `posts/*.md` 转换为静态博客页面（`generate_blog.py`）。

该仓库提供可配置的脚本、示例输出文件以及一个简洁的博客模板，方便用于个人主页、项目简介和笔记整理。

---

## 快速开始

1. 克隆仓库并进入目录：

```bash
git clone <repo-url>
cd XiGua
```

2. 生成个人简介（默认生成 `INTRO.md` 与 `index.html`）：

```bash
python3 generate_intro.py
```

你可以指定语言：生成中文、英文或双语（默认为中文）：

```bash
python3 generate_intro.py --lang zh        # 仅中文（默认）
python3 generate_intro.py --lang en        # 仅英文
python3 generate_intro.py --lang both      # 中英双语
```

3. 生成预览（可选）：

```bash
python3 generate_intro.py --out-preview PREVIEW.md
```

4. 生成博客页面（需要 `markdown` 包）：

```bash
pip3 install markdown
python3 generate_blog.py
```

生成后的静态博客页面位于 `blog/` 目录。

---

## 文件结构（简要）

- `generate_intro.py` — 生成个人简介的 Markdown / HTML / 预览
- `generate_blog.py` — 将 `posts/*.md` 转为 `blog/*.html`
- `posts/` — 博客文章（Markdown）
- `blog/` — 生成的静态页面输出
- `INTRO.md`, `index.html`, `PREVIEW.md` — 示例输出
- `USAGE.md` — 详细使用说明

---

## 自定义与扩展

- 模板：可编辑 `blog/template.html` 或 `generate_intro.py` 中的模板以更改样式与内容结构。
- 发布：可以把 `blog/` 目录部署到 GitHub Pages、Netlify 或其他静态站点托管服务。
- 自动化：仓库包含 GitHub Actions 工作流（CI 与 GitHub Pages 自动部署）。
- 安装为包（开发阶段）：

```bash
pip install -e .
# 之后可以使用命令行工具
generate-intro --help
generate-blog --help
```

---

## 许可证

默认未包含完整许可证文本。若需要可添加 `LICENSE` 文件（建议 MIT 或其它开源许可证）。

---

## 联系方式

Bilibili: https://space.bilibili.com/402631059?spm_id_from=333.1007.0.0

---

如果你希望我把 `README.md` 调整为更精简或更详细的版本，或加入自动部署示例与 CI 配置，告诉我你的偏好。
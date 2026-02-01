# XiGua — Documentation

详细文档（包含安装、使用、部署和 CI 说明）。

## 快速开始

1. 克隆仓库并进入目录：

```bash
git clone https://github.com/dyxiguajun/XiGua.git
cd XiGua
```

2. 安装依赖并运行生成脚本：

```bash
pip install -r requirements.txt
python3 generate_intro.py              # 生成简介（INTRO.md, index.html）
python3 generate_blog.py               # 生成 blog/ 静态页面
```

3. 本地测试：

```bash
pytest -q
```

## 功能与文件结构

- `generate_intro.py` — 生成个人简介的 Markdown / HTML / 预览
- `generate_blog.py` — 将 `posts/*.md` 转为 `blog/*.html`
- `posts/` — 博客文章（Markdown）
- `blog/` — 生成的静态页面输出

## 部署与 CI

- 本仓库使用 GitHub Actions：`ci.yml`（测试）与 `pages.yml`（生成并部署 `blog/` 到 GitHub Pages）。

示例部署片段（最小示例）：

```yaml
name: Pages
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          publish_dir: ./blog
```

在 `.github/workflows/pages.yml` 中有更完整的实现（包含 coverage 发布与部署细节）。

## 故障排查（常见）

- 未安装依赖：运行 `pip install -r requirements.txt`。
- `posts/` 为空：确认至少有一篇 Markdown 文件（`YYYY-MM-DD-title.md`）。
- Pages 部署 404：查看 Pages workflow 日志并确认 `blog/` 已成功推送到 `gh-pages` 分支。

## 联系方式

- Bilibili: https://space.bilibili.com/402631059?spm_id_from=333.1007.0.0

如需改进文档或 CI 配置，请通过 Issue 或 PR 提出。欢迎贡献！

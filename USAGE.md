# 使用说明

[![CI](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml) [![Pages](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml)

站点：https://dyxiguajun.github.io/XiGua/

这是一个用于生成个人简介和静态博客的小工具集：
- 生成简介：`generate_intro.py` 会输出 `INTRO.md`（Markdown）和 `index.html`（HTML）。
- 生成博客：`generate_blog.py` 会把 `posts/*.md` 转为 `blog/*.html`。

快速示例

生成简介：
```bash
python3 generate_intro.py --out-md INTRO.md --out-html index.html
```

生成博客：
```bash
pip install -r requirements.txt
python3 generate_blog.py
```

主要 CLI 参数（常用）

- `--school`：学校（默认：俄勒冈州立大学）
- `--status`：身份（默认：留学生）
- `--role`：角色（默认：全栈开发者 & 在校学生）
- `--language`：主要语言（默认：Python）
- `--years`：经验年限（默认：3 年）
- `--iot` / `--no-iot`：是否有物联网经验（默认：有）
- `--learning`：正在学习（默认：HarmonyOS）
- `--bilibili`：Bilibili 链接
- `--lang`：输出语言（`zh` | `en` | `both`，默认：`zh`）

示例：
```bash
python3 generate_intro.py --language "Python, JavaScript" --years "4 年" --out-md my_intro.md
```

部署与 CI

- CI（`.github/workflows/ci.yml`）会在 push/PR 时运行测试并检查功能。
- Pages（`.github/workflows/pages.yml`）会在 push 到 `main` 时生成 `blog/` 并部署到 GitHub Pages。

故障排查（简要）

1. 查看仓库的 **Actions**：打开失败的 workflow，查看具体日志。  
2. 常见问题：未安装依赖（运行 `pip install -r requirements.txt`）或 `posts/` 目录为空。  
3. 本地复现：运行 `python3 generate_blog.py` 或 `pytest` 来定位问题。  
4. 部署问题：确认 `blog/` 已正确生成，检查 Pages workflow 的上传/部署步骤日志。

需要更详细的说明或把某些检查自动化（例如在 CI 中增加通知或保存更多 artifact）可以在 issue 或 PR 中提出改进建议。
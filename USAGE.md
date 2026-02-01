# 使用说明

[![CI](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/ci.yml) [![Pages](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml/badge.svg)](https://github.com/dyxiguajun/XiGua/actions/workflows/pages.yml)

项目站点（GitHub Pages）：https://dyxiguajun.github.io/XiGua/

这是一个简单脚本，用来生成个人简介的 `INTRO.md`（Markdown）和 `index.html`（HTML）。

运行示例：

```bash
python3 generate_intro.py --out-md INTRO.md --out-html index.html
```

可用参数（示例）：

- `--school` 学校，默认：俄勒冈州立大学（Oregon State University）
- `--status` 身份，默认：留学生
- `--role` 角色，默认：全栈开发者 & 在校学生
- `--language` 主要语言，默认：Python
- `--years` 开发经验年限，默认：3 年
- `--iot` 指定此参数表示有物联网经验（默认开启）
- `--learning` 正在学习的技术，默认：HarmonyOS
- `--bilibili` Bilibili 链接
- `--lang` 输出语言（`zh` / `en` / `both`，默认为 `zh`）

示例：

```bash
python3 generate_intro.py --language "Python, JavaScript" --years "4 年" --out-md my_intro.md
```

生成博客页面（示例）：

```bash
# 推荐在虚拟环境中安装依赖
pip3 install -r requirements.txt

# 生成博客静态页面（会把 posts/*.md 转换到 blog/）
python3 generate_blog.py
```

或者在安装为包后使用命令行工具：

```bash
pip install -e .
generate-blog
```

注意：`generate_blog.py` 支持使用自定义输出目录与模板（`--out` / `--template` CLI 参数）。如果需要我可以添加更多部署或主题支持。

## CI 与部署说明

- 徽章说明：顶部的 **CI** 徽章表示 GitHub Actions 的测试工作流（`ci.yml`）状态；**Pages** 徽章表示 GitHub Pages 部署工作流（`pages.yml`）的最近部署状态。
- CI 做了什么：`ci.yml` 会在每次 push/PR 到 `main` 时运行，安装依赖并执行 `pytest`（确保变更不会破坏生成逻辑）。
- 自动部署：`pages.yml` 会在 push 到 `main` 时运行，执行 `generate_blog.py` 生成 `blog/`，并将生成内容部署到 GitHub Pages（仓库的 Pages 设置中可以看到站点 URL）。

故障排查（快速步骤）：
1. 查看 Actions 选项卡：打开仓库的 **Actions**，选择失败的 workflow，查看日志并定位报错步骤。  
2. 常见问题：依赖未安装（检查 `pip install -r requirements.txt`），或 `posts/` 为空（生成器会期望至少一个 Markdown 文件）。  
3. 本地复现：在本地运行 `python3 generate_blog.py` 或 `pytest` 来复现并调试问题。  
4. 部署问题：如果 Pages 部署失败，检查 `Upload artifact` 与 `Deploy to GitHub Pages` 步骤的日志，确认 `blog/` 目录已正确生成并上传。  

如果你希望我把这些排查步骤自动化（例如在 CI 中添加更详细的错误输出或通知），我可以为 workflow 添加更详细的日志与失败提醒。
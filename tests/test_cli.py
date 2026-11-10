from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from xigua.cli import main


def test_init_creates_a_site(tmp_path: Path, capsys) -> None:
    target = tmp_path / "my-site"
    code = main(["init", str(target), "--title", "我的站点"])
    assert code == 0
    assert (target / "xigua.toml").is_file()
    assert (target / "posts" / "welcome.md").is_file()
    text = (target / "xigua.toml").read_text(encoding="utf-8")
    assert 'title = "我的站点"' in text
    assert "已创建站点" in capsys.readouterr().out


def test_init_refuses_to_overwrite(tmp_path: Path, capsys) -> None:
    target = tmp_path / "site"
    assert main(["init", str(target)]) == 0
    assert main(["init", str(target)]) == 1
    assert "--force" in capsys.readouterr().err


def test_init_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "site"
    assert main(["init", str(target)]) == 0
    (target / "posts" / "welcome.md").write_text("changed", encoding="utf-8")
    assert main(["init", str(target), "--force"]) == 0
    assert "XiGua" in (target / "posts" / "welcome.md").read_text(encoding="utf-8")


def test_new_creates_post(tmp_path: Path, capsys) -> None:
    target = tmp_path / "site"
    assert main(["init", str(target)]) == 0
    code = main(
        [
            "new",
            "第一篇文章",
            "--site",
            str(target),
            "--date",
            "2026-02-14",
            "--tags",
            "Python, 笔记",
        ]
    )
    assert code == 0
    path = target / "posts" / "2026-02-14-第一篇文章.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "title: 第一篇文章" in text
    assert "2026-02-14" in text
    assert "- Python" in text


def test_new_rejects_bad_date(tmp_path: Path, capsys) -> None:
    target = tmp_path / "site"
    main(["init", str(target)])
    assert main(["new", "x", "--site", str(target), "--date", "14/02/2026"]) == 1
    assert "YYYY-MM-DD" in capsys.readouterr().err


def test_build_and_check(tmp_path: Path, capsys) -> None:
    target = tmp_path / "site"
    main(["init", str(target)])
    code = main(["build", "--site", str(target)])
    assert code == 0
    out = capsys.readouterr().out
    assert "完成" in out
    assert (target / "dist" / "index.html").is_file()
    assert (target / "dist" / "feed.xml").is_file()

    assert main(["check", "--site", str(target)]) == 0
    out = capsys.readouterr().out
    assert "文章：1 篇" in out


def test_check_warns_about_missing_url(tmp_path: Path, capsys) -> None:
    target = tmp_path / "site"
    main(["init", str(target)])
    assert main(["check", "--site", str(target)]) == 0
    out = capsys.readouterr().out
    assert "site.url" in out


def test_missing_config_is_a_clean_error(tmp_path: Path, capsys) -> None:
    assert main(["build", "--site", str(tmp_path)]) == 1
    assert "xigua.toml" in capsys.readouterr().err


def test_module_entrypoint(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "xigua", "--version"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "xigua 1.0.0" in result.stdout

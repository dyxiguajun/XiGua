import subprocess
import sys
from pathlib import Path

def test_generate_intro_cli(tmp_path, monkeypatch):
    out_md = tmp_path / 'intro.md'
    out_html = tmp_path / 'intro.html'
    cmd = [sys.executable, 'generate_intro.py', '--out-md', str(out_md), '--out-html', str(out_html)]

    res = subprocess.run(cmd, check=True)
    assert res.returncode == 0
    assert out_md.exists()
    assert out_html.exists()


def test_generate_blog_cli(tmp_path):
    posts = tmp_path / 'posts'
    posts.mkdir()
    p = posts / '2026-01-01-cli-post.md'
    p.write_text('# CLI Post\n\nHello', encoding='utf-8')

    cmd = [sys.executable, 'generate_blog.py', '--posts', str(posts), '--out', str(tmp_path / 'out')]
    res = subprocess.run(cmd, check=True)
    assert res.returncode == 0
    assert (tmp_path / 'out' / 'cli-post.html').exists() or any((tmp_path / 'out').glob('*.html'))

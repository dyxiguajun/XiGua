import pathlib
import tempfile
from generate_blog import build


def test_build_writes_html(tmp_path):
    posts_dir = tmp_path / 'posts'
    posts_dir.mkdir()
    # create a sample post
    p = posts_dir / '2026-01-01-sample.md'
    p.write_text('# Sample Post\n\nHello world', encoding='utf-8')

    template = tmp_path / 'template.html'
    template.write_text('<html><head><title>{title}</title></head><body>{content}</body></html>', encoding='utf-8')

    out_dir = tmp_path / 'out'
    build(out_dir=out_dir, posts_dir=posts_dir, template_path=template)

    # check generated files
    assert (out_dir / 'sample-post.html').exists() or any(out_dir.glob('*.html'))
    assert (out_dir / 'index.html').exists()
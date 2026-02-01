from generate_blog import parse_post, slugify


def test_parse_post_title_and_date():
    md = """# My Post\n\nContent here."""
    meta = parse_post(md, "2026-01-01-my-post.md")
    assert meta['title'] == 'My Post'
    assert meta['date'] == '2026-01-01'


def test_slugify_basic():
    assert slugify('Hello World') == 'hello-world'
    assert slugify('Café') == 'cafe'

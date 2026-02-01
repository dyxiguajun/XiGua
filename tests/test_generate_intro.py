import datetime
from generate_intro import render_preview, render_markdown, render_html


def test_render_preview_contains_expected_fields():
    ctx = {
        'school': 'Test University',
        'status': '学生',
        'role': '开发者',
        'language': 'Python',
        'years': '2 年',
        'iot': True,
        'learning': 'HarmonyOS',
        'bilibili': 'https://example.com',
        'lang': 'both',
    }
    text = render_preview(ctx)
    assert 'Test University' in text
    assert 'Python' in text
    assert '具有物联网' in text or 'IoT' in text
    assert datetime.date.today().isoformat() in text


def test_render_markdown_language_selection():
    base = {
        'school': 'Test University',
        'status': '学生',
        'role': '开发者',
        'language': 'Python',
        'years': '2 年',
        'iot': False,
        'learning': 'HarmonyOS',
        'bilibili': 'https://example.com',
    }

    md_zh = render_markdown({**base, 'lang': 'zh'})
    assert '## 自我介绍' in md_zh
    assert '## About' not in md_zh
    assert '暂无物联网经验' in md_zh

    md_en = render_markdown({**base, 'lang': 'en'})
    assert '## About' in md_en
    assert '## 自我介绍' not in md_en
    assert '暂无物联网经验' not in md_en

    md_both = render_markdown({**base, 'lang': 'both'})
    assert '## 自我介绍' in md_both and '## About' in md_both


def test_render_html_language_selection():
    base = {
        'school': 'Test University',
        'status': '学生',
        'role': '开发者',
        'language': 'Python',
        'years': '2 年',
        'iot': False,
        'learning': 'HarmonyOS',
        'bilibili': 'https://example.com',
    }

    html_zh = render_html({**base, 'lang': 'zh'})
    assert '<h2>自我介绍' in html_zh
    assert 'About' not in html_zh
    # bilibili link should open safely
    assert 'rel="noopener noreferrer"' in html_zh

    html_en = render_html({**base, 'lang': 'en'})
    assert '<h2>About' in html_en
    assert '自我介绍' not in html_en
    assert 'rel="noopener noreferrer"' in html_en

    html_both = render_html({**base, 'lang': 'both'})
    assert '自我介绍' in html_both and 'About' in html_both
    assert 'rel="noopener noreferrer"' in html_both


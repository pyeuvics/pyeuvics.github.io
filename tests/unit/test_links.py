from __future__ import annotations


import pytest

from tools.site_assembly.pipeline import (
    _css_targets,
    _RenderedLinkParser,
    _srcset_targets,
)



def test_rendered_resource_lists_ignore_css_comments_and_preserve_data_urls() -> None:
    assert _css_targets(
        "/* background: url(../private.png); */ background: url(public.png)"
    ) == ["public.png"]
    assert _srcset_targets(
        "data:image/png;base64,AAAA 1x, public.png 2x"
    ) == ["data:image/png;base64,AAAA", "public.png"]


@pytest.mark.parametrize(
    ("html", "unsafe"),
    [
        ('<script type="math/tex">a_0</script>', False),
        ('<script type="math/tex; mode=display">a_0</script>', False),
        ("<script>alert(1)</script>", True),
        ('<script type="text/javascript">alert(1)</script>', True),
        ('<script type="math/tex" src="evil.js"></script>', True),
        ('<iframe src="https://example.org"></iframe>', True),
    ],
)
def test_rendered_link_parser_only_allows_inert_math_script_tags(
    html: str, unsafe: bool
) -> None:
    parser = _RenderedLinkParser()
    parser.feed(html)
    assert parser.unsafe_active_content is unsafe

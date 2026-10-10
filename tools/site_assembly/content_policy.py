"""Reviewed source-fragment HTML, CSS and resource URL policy.

This policy applies to imported content, not to the trusted website theme.
Only raster image data URLs are admitted; HTML/SVG data and browser-active
contexts are excluded. CSS is parsed with tinycss2 rather than regex matching.
"""
from __future__ import annotations

import base64
import binascii
from enum import Enum
from html import unescape
from html.parser import HTMLParser
import re
import math
from typing import Any
from urllib.parse import unquote, urlsplit

import tinycss2  # type: ignore[import-untyped]  # tinycss2 has no bundled type declarations.


class ContentPolicyError(ValueError):
    """Source markup falls outside the reviewed inert publication subset."""


class URLUse(Enum):
    NAVIGATION = 'navigation'
    IMAGE = 'image'
    RESOURCE = 'resource'


SAFE_MATH_TYPE = re.compile(r'^math/tex(?:\s*;\s*mode\s*=\s*display\s*)?$', re.I)
RASTER_DATA = re.compile(r'^data:image/(png|jpeg|gif|webp);base64,([A-Za-z0-9+/=]+)$', re.I)


def validate_url(value: str, use: URLUse) -> None:
    normalized = value
    for _ in range(4):
        decoded = unquote(unescape(normalized))
        if decoded == normalized:
            break
        normalized = decoded
    normalized = re.sub(r'[\x00-\x20\x7f]', '', normalized)
    if '\\' in normalized:
        raise ContentPolicyError('unsafe or unsupported link scheme or backslash')
    try:
        parsed = urlsplit(normalized)
    except ValueError as exc:
        raise ContentPolicyError('invalid resource URL') from exc
    scheme = parsed.scheme.lower()
    if scheme == 'data':
        match = RASTER_DATA.fullmatch(value.strip()) if use is URLUse.IMAGE else None
        if match is None:
            raise ContentPolicyError('unsafe data URL context or image format')
        try:
            payload = base64.b64decode(match[2], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ContentPolicyError('invalid image data encoding') from exc
        signatures = {'png': b'\x89PNG\r\n\x1a\n', 'jpeg': b'\xff\xd8\xff', 'gif': b'GIF8', 'webp': b'RIFF'}
        if not payload.startswith(signatures[match[1].lower()]) or (match[1].lower() == 'webp' and payload[8:12] != b'WEBP'):
            raise ContentPolicyError('image data does not match its declared format')
        return
    allowed = {'', 'http', 'https'}
    if use is URLUse.NAVIGATION:
        allowed |= {'mailto', 'tel', 'ftp', 'ftps'}
    if scheme not in allowed:
        raise ContentPolicyError('unsafe or unsupported link scheme')


CSS_PROPERTIES = frozenset('''color background background-color background-image
width height min-width min-height max-width max-height display opacity
font font-family font-size font-style font-weight line-height letter-spacing
text-align text-decoration text-indent white-space vertical-align
margin margin-top margin-right margin-bottom margin-left
padding padding-top padding-right padding-bottom padding-left
border border-top border-right border-bottom border-left border-color border-style border-width border-radius
paint-order text-anchor rx ry fill stroke stroke-width stroke-linecap stroke-linejoin stroke-dasharray stroke-dashoffset fill-opacity stroke-opacity overflow overflow-x overflow-y'''.split())
CSS_FUNCTIONS = {'rgb', 'rgba', 'hsl', 'hsla', 'calc', 'min', 'max', 'clamp', 'linear-gradient', 'radial-gradient'}


def _css_values(tokens: list[Any], depth: int = 0) -> list[str]:
    if depth > 16:
        raise ContentPolicyError('unsupported CSS nesting depth')
    targets: list[str] = []
    for token in tokens:
        kind = token.type
        if kind == 'url':
            validate_url(token.value, URLUse.IMAGE)
            targets.append(token.value)
        elif kind == 'function':
            name = token.lower_name
            if name == 'url':
                args = [item for item in token.arguments if item.type not in {'whitespace', 'comment'}]
                if len(args) != 1 or args[0].type != 'string':
                    raise ContentPolicyError('unsupported CSS URL syntax')
                validate_url(args[0].value, URLUse.IMAGE)
                targets.append(args[0].value)
            elif name in CSS_FUNCTIONS:
                targets.extend(_css_values(token.arguments, depth + 1))
            else:
                raise ContentPolicyError('unsupported or executable CSS function')
        elif kind not in {'whitespace', 'comment', 'ident', 'string', 'number', 'percentage', 'dimension', 'hash', 'literal'}:
            raise ContentPolicyError('unsupported CSS syntax')
    return targets


def css_targets(value: str) -> list[str]:
    targets: list[str] = []
    for declaration in tinycss2.parse_declaration_list(value, skip_comments=True, skip_whitespace=True):
        if declaration.type != 'declaration' or declaration.lower_name not in CSS_PROPERTIES:
            raise ContentPolicyError('unsupported CSS declaration or at-rule')
        targets.extend(_css_values(declaration.value))
    return targets


def srcset_targets(value: str) -> list[str]:
    """A bounded subset: URLs with optional positive width/density descriptors."""
    targets: list[str] = []
    offset = 0
    while offset < len(value):
        while offset < len(value) and value[offset] in ' \t\r\n,':
            offset += 1
        start = offset
        while offset < len(value) and not value[offset].isspace():
            offset += 1
        raw = value[start:offset]
        target = raw.rstrip(',')
        if not target:
            continue
        targets.append(target)
        if raw.endswith(','):
            continue
        start = offset
        while offset < len(value) and value[offset] != ',':
            offset += 1
        descriptor = value[start:offset].strip()
        if descriptor and not re.fullmatch(r'(?:[1-9][0-9]*w|(?:[0-9]+(?:\.[0-9]+)?)x)', descriptor):
            raise ContentPolicyError('unsupported srcset descriptor')
        if descriptor.endswith('x') and (not math.isfinite(float(descriptor[:-1])) or float(descriptor[:-1]) <= 0):
            raise ContentPolicyError('srcset density must be positive')
        offset += offset < len(value)
    return targets


HTML_TAGS = frozenset('''a abbr b bdi bdo blockquote br caption code col colgroup dd del details dfn div dl dt em figcaption figure h1 h2 h3 h4 h5 h6 hr i img ins kbd li mark ol p picture pre q rp rt ruby s samp section small source span strong sub summary sup table tbody td th thead time tr u ul var video audio wbr script'''.split())
SVG_TAGS = frozenset('''svg marker g path rect circle ellipse line polyline polygon text tspan defs symbol use image title desc clippath mask lineargradient radialgradient stop pattern'''.split())
GLOBALS = {'id', 'class', 'title', 'lang', 'dir', 'role', 'style', 'markdown'}
TAG_ATTRIBUTES = {
    'a': {'href', 'target', 'rel', 'download', 'hreflang', 'type'},
    'img': {'src', 'srcset', 'sizes', 'alt', 'width', 'height', 'loading', 'decoding'},
    'source': {'src', 'srcset', 'sizes', 'type', 'media'},
    'video': {'src', 'poster', 'controls', 'width', 'height', 'preload', 'muted', 'loop'},
    'audio': {'src', 'controls', 'preload', 'muted', 'loop'},
    'script': {'type'}, 'blockquote': {'cite'}, 'q': {'cite'},
    'del': {'cite', 'datetime'}, 'ins': {'cite', 'datetime'},
    'time': {'datetime'}, 'ol': {'start', 'reversed', 'type'}, 'li': {'value'},
    'details': {'open'}, 'td': {'colspan', 'rowspan', 'headers', 'align'},
    'th': {'colspan', 'rowspan', 'headers', 'scope', 'align'},
    'col': {'span', 'width'}, 'colgroup': {'span', 'width'},
}
SVG_ATTRIBUTES = frozenset('''xmlns xmlns:xlink xml:space version viewbox preserveaspectratio marker-start marker-mid marker-end markerwidth markerheight markerunits orient refx refy dx dy width height x y x1 y1 x2 y2 cx cy r rx ry d points transform fill fill-rule fill-opacity stroke stroke-width stroke-linecap stroke-linejoin stroke-dasharray stroke-opacity opacity text-anchor dominant-baseline font-size font-family font-weight href xlink:href offset stop-color stop-opacity gradientunits gradienttransform patternunits patterntransform clippathunits maskunits clip-path mask'''.split())


class RenderedLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []
        self.unsafe_active_content = False
        self.error: str | None = None

    def _add(self, target: str, use: URLUse) -> None:
        validate_url(target, use)
        self.targets.append(target)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        try:
            self._start(tag.lower(), attrs)
        except (ContentPolicyError, ValueError) as exc:
            self.unsafe_active_content = True
            self.error = self.error or str(exc)

    def _start(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value for name, value in attrs}
        if tag not in HTML_TAGS | SVG_TAGS or len(attributes) != len(attrs):
            raise ContentPolicyError('unsafe active content or unsupported element/duplicate attribute')
        if tag == 'script' and not SAFE_MATH_TYPE.fullmatch((attributes.get('type') or '').strip()):
            raise ContentPolicyError('unsafe active content: executable script')
        allowed = GLOBALS | TAG_ATTRIBUTES.get(tag, set())
        if tag in SVG_TAGS:
            allowed |= SVG_ATTRIBUTES
        for name, value in attrs:
            name = name.lower()
            if name not in allowed and not name.startswith(('aria-', 'data-')):
                raise ContentPolicyError('unsafe active content or unsupported attribute')
            if value is None:
                continue
            if name == 'style':
                self.targets.extend(css_targets(value))
            elif name == 'srcset':
                for target in srcset_targets(value):
                    self._add(target, URLUse.IMAGE)
            elif name in {'href', 'xlink:href', 'src', 'poster', 'cite'}:
                use = URLUse.NAVIGATION if tag in {'a', 'blockquote', 'q', 'del', 'ins'} else URLUse.RESOURCE
                if tag in {'img', 'image', 'source'} or name == 'poster':
                    use = URLUse.IMAGE
                self._add(value, use)
            elif tag in SVG_TAGS and name in {'fill', 'stroke', 'clip-path', 'mask', 'marker-start', 'marker-mid', 'marker-end'}:
                # SVG paint/reference values use the same CSS token parser.
                self.targets.extend(_css_values(tinycss2.parse_component_value_list(value)))


def parse_fragment(html: str) -> RenderedLinkParser:
    parser = RenderedLinkParser()
    parser.feed(html)
    parser.close()
    if parser.error is not None:
        raise ContentPolicyError(parser.error)
    return parser

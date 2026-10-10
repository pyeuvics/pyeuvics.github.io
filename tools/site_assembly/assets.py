"""Bounded format inspection; admission and ownership are separate prerequisites."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import subprocess
import sys
from typing import Any, Literal
from urllib.parse import unquote, urlsplit
import zlib

from defusedxml import ElementTree as SafeXML  # type: ignore[import-untyped]
from PIL import Image
import tinycss2  # type: ignore[import-untyped]
import yaml

from tools.privacy import ScanProfile, scan_bytes, scan_text
from .content_policy import RenderedLinkParser, SVG_TAGS, URLUse, css_targets, validate_url
from .structured import UniqueSafeLoader, _pairs, _nonfinite

MAX_FILE = 32 * 1024 * 1024
MAX_TEXT = 8 * 1024 * 1024
MAX_NODES = 100_000
MAX_PIXELS = 20_000_000
Origin = Literal['source', 'website', 'theme']


class AssetError(ValueError):
    """An owned asset cannot be completely inspected under the format policy."""


def inspect_strings(value: Any) -> None:
    pending = [(value, 0)]
    seen: set[int] = set()
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > MAX_NODES or depth > 64:
            raise AssetError('asset structure exceeds inspection limits')
        if isinstance(item, str):
            scan_text(item, 'decoded asset text', ScanProfile.PUBLIC)
        elif isinstance(item, bytes):
            scan_bytes(item, 'decoded asset bytes', ScanProfile.PUBLIC)
            for encoding in ('utf-16-le', 'utf-16-be'):
                if len(item) % 2 == 0:
                    scan_text(item.decode(encoding, errors='replace'), 'decoded metadata', ScanProfile.PUBLIC)
        elif isinstance(item, (dict, list, tuple)):
            if id(item) in seen:
                raise AssetError('shared or recursive asset structure is unsupported')
            seen.add(id(item))
            values = list(item.keys()) + list(item.values()) if isinstance(item, dict) else item
            pending.extend((child, depth + 1) for child in values)
        elif isinstance(item, float):
            import math
            if not math.isfinite(item):
                raise AssetError('non-finite asset number')


def _reference(target: str, relative: str, approved: frozenset[str], ids: set[str] | None = None, *, navigation: bool = False) -> None:
    validate_url(target, URLUse.NAVIGATION if navigation else URLUse.IMAGE)
    parsed = urlsplit(unquote(target))
    if parsed.scheme == 'data':
        payload = base64.b64decode(target.split(',', 1)[1], validate=True)
        _raster(payload, '.' + target.split(';', 1)[0].split('/')[-1])
    elif parsed.scheme or parsed.netloc:
        if not navigation:
            raise AssetError('external asset resources are unsupported')
    elif parsed.path:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(relative), parsed.path))
        if parsed.path.startswith('/') or path not in approved:
            raise AssetError('asset reference is not an admitted unchanged-route resource')
    elif parsed.fragment and ids is not None and parsed.fragment not in ids:
        raise AssetError('asset fragment reference is missing')


def _stylesheet(text: str, origin: Origin, relative: str, approved: frozenset[str], ids: set[str] | None = None) -> None:
    rules = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
    if origin != 'source':
        # Theme/website bytes have a separately verified origin. Still inspect
        # decoded tokens (including escaped strings) and reject parser errors.
        pending = [(rule, 0) for rule in rules]
        count = 0
        while pending:
            token, depth = pending.pop(); count += 1
            if count > MAX_NODES or depth > 64 or token.type == 'error':
                raise AssetError('CSS exceeds structural inspection limits')
            for field in ('value', 'name'):
                value = getattr(token, field, None)
                if isinstance(value, str): inspect_strings(value)
            for field in ('prelude', 'content', 'arguments'):
                pending.extend((child, depth + 1) for child in getattr(token, field, None) or [])
        return
    for rule in rules:
        if rule.type != 'qualified-rule':
            raise AssetError('source CSS at-rules or malformed rules are unsupported')
        for target in css_targets(tinycss2.serialize(rule.content)):
            _reference(target, relative, approved, ids)


def _svg(data: bytes, relative: str, approved: frozenset[str]) -> None:
    root = SafeXML.fromstring(data, forbid_entities=True, forbid_external=True)
    svg = '{http://www.w3.org/2000/svg}'
    if root.tag != svg + 'svg':
        raise AssetError('invalid SVG namespace/root')
    ids = {node.attrib['id'] for node in root.iter() if 'id' in node.attrib}
    pending = [(root, 0, False)]; count = 0
    metadata_namespaces = ('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}', '{http://purl.org/dc/elements/1.1/}', '{http://creativecommons.org/ns#}')
    while pending:
        node, depth, metadata = pending.pop(); count += 1
        if count > MAX_NODES or depth > 64:
            raise AssetError('SVG exceeds structural inspection limits')
        tag = node.tag.removeprefix(svg).lower()
        inert_metadata = metadata and node.tag.startswith(metadata_namespaces)
        if not inert_metadata and (not node.tag.startswith(svg) or tag not in SVG_TAGS | {'a', 'style', 'metadata'}):
            raise AssetError('unsafe or unsupported SVG element')
        inspect_strings([node.text or '', node.tail or '', dict(node.attrib)])
        if not inert_metadata:
            attrs = [(name.replace('{http://www.w3.org/1999/xlink}', 'xlink:').replace('{http://www.w3.org/XML/1998/namespace}', 'xml:'), value) for name, value in node.attrib.items()]
            if tag == 'style':
                if any(name != 'type' or value != 'text/css' for name, value in attrs):
                    raise AssetError('unsupported SVG stylesheet attributes')
                _stylesheet(node.text or '', 'source', relative, approved, ids)
            elif tag == 'metadata':
                if attrs: raise AssetError('unsupported SVG metadata attributes')
            else:
                parser = RenderedLinkParser(); parser._start(tag, attrs)
                for target in parser.targets:
                    _reference(target, relative, approved, ids, navigation=tag == 'a')
        pending.extend((child, depth + 1, inert_metadata or tag == 'metadata') for child in node)


def _raster(data: bytes, suffix: str) -> None:
    formats = {'.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG', '.gif': 'GIF', '.webp': 'WEBP', '.ico': 'ICO'}
    with Image.open(io.BytesIO(data)) as picture:
        if picture.format != formats[suffix]: raise AssetError('raster format does not match extension')
        frames = getattr(picture, 'n_frames', 1)
        if frames > 100 or picture.width * picture.height * frames > MAX_PIXELS:
            raise AssetError('raster exceeds decoded pixel limit')
        picture.verify()
    with Image.open(io.BytesIO(data)) as picture:
        pixels = 0
        for frame in range(getattr(picture, 'n_frames', 1)):
            picture.seek(frame); pixels += picture.width * picture.height
            if pixels > MAX_PIXELS: raise AssetError('raster exceeds decoded pixel limit')
            inspect_strings(dict(picture.info)); inspect_strings(dict(picture.getexif()))
            picture.load()


def _xml(data: bytes) -> None:
    root = SafeXML.fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    if root.tag not in {namespace + 'urlset', namespace + 'sitemapindex'}:
        raise AssetError('unsupported XML output')
    pending = [(root, 0)]; count = 0
    while pending:
        node, depth = pending.pop(); count += 1
        if count > MAX_NODES or depth > 64: raise AssetError('XML exceeds inspection limits')
        if node.tag not in {namespace + name for name in ('urlset', 'sitemapindex', 'url', 'sitemap', 'loc', 'lastmod', 'changefreq', 'priority')} or node.attrib:
            raise AssetError('unsupported sitemap element/attribute')
        inspect_strings([node.text or '', node.tail or '', dict(node.attrib)])
        if node.tag == namespace + 'loc': validate_url(node.text or '', URLUse.NAVIGATION)
        pending.extend((child, depth + 1) for child in node)


def _inspect(data: bytes, suffix: str, origin: Origin, relative: str, approved: frozenset[str]) -> None:
    scan_bytes(data, 'asset bytes', ScanProfile.PUBLIC)
    if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico'}:
        _raster(data, suffix)
    elif suffix == '.gz':
        inner = PurePosixPath(relative).with_suffix('')
        if inner.suffix not in {'.xml', '.json', '.map', '.txt'}: raise AssetError('unsupported compressed output')
        decoder = zlib.decompressobj(31)
        plain = decoder.decompress(data, MAX_TEXT + 1)
        if len(plain) > MAX_TEXT or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise AssetError('compressed output exceeds limits or is incomplete')
        _inspect(plain, inner.suffix, origin, str(inner), approved)
    else:
        if len(data) > MAX_TEXT: raise AssetError('text asset exceeds inspection limit')
        text = data.decode('utf-8')
        if suffix == '.svg': _svg(data, relative, approved)
        elif suffix == '.css': _stylesheet(text, origin, relative, approved)
        elif suffix in {'.json', '.map', '.ipynb'}:
            value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
            inspect_strings(value)
            if suffix == '.map' and (not isinstance(value, dict) or value.get('version') != 3 or not isinstance(value.get('sources'), list) or not isinstance(value.get('mappings'), str)):
                raise AssetError('unsupported source map structure')
        elif suffix in {'.yaml', '.yml', '.cff'}: inspect_strings(yaml.load(text, Loader=UniqueSafeLoader))
        elif suffix == '.xml': _xml(data)
        elif suffix in {'.js', '.html'} and origin == 'source': raise AssetError('imported browser-active assets are unsupported')
        elif suffix not in {'', '.js', '.html', '.md', '.txt', '.csv', '.tex', '.bib', '.py'}:
            raise AssetError('unsupported asset format')


def validate_asset(path: Path, *, origin: Origin = 'source', relative: str | None = None, approved: frozenset[str] = frozenset()) -> None:
    try:
        if path.is_symlink(): raise AssetError('asset symlink is unsupported')
        with path.open('rb') as stream: data = stream.read(MAX_FILE + 1)
        if len(data) > MAX_FILE: raise AssetError('asset exceeds file size limit')
        if path.suffix.lower() == '.pdf':
            subprocess.run([sys.executable, '-m', 'tools.validate_pdf_asset', str(path.resolve())], cwd=Path(__file__).resolve().parents[2], check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            _inspect(data, path.suffix.lower(), origin, relative or path.name, approved)
    except Exception as exc:
        raise AssetError('asset fails bounded format/privacy validation') from exc

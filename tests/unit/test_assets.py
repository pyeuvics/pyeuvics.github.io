"""Synthetic adversarial format cases; approved bytes remain unchanged."""
import gzip
import hashlib
import io
from pathlib import Path

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
import pytest

from tests.support.publication import generic_pdf
from tools.site_assembly import assets


@pytest.mark.parametrize(('suffix','data'), [
    ('.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'),
    ('.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><foreignObject/></svg>'),
    ('.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.org/track.png"/></svg>'),
    ('.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><use href="#missing"/></svg>'),
    ('.svg', b'<!DOCTYPE svg [<!ENTITY x "secret">]><svg xmlns="http://www.w3.org/2000/svg">&x;</svg>'),
    ('.css', br'p { background: u\72l(javascript:alert); }'),
    ('.css', b'@import "https://example.org/style.css";'),
    ('.css', b'p { background-image: url(missing.png); }'),
    ('.json', br'{"name":"\u002fUsers\u002falice\u002fprivate"}'),
    ('.json', b'{"a":1,"a":2}'),
    ('.json', b'{"x":NaN}'),
    ('.map', b'{"version":2,"sources":[],"mappings":""}'),
    ('.yaml', b'node: &a [*a]'),
    ('.png', b'\x89PNG\r\n\x1a\ninvalid'),
    ('.js', b'alert(1)'),
    ('.xml.gz', gzip.compress(b'<broken>')),
    ('.txt.gz', gzip.compress(b'public') + gzip.compress(b'hidden')),
    ('.txt.gz', gzip.compress(b'/Users/alice/private')),
])
def test_unsafe_assets_fail_without_echoing_payload(tmp_path: Path, suffix: str, data: bytes) -> None:
    path=tmp_path/('fixture'+suffix);path.write_bytes(data)
    with pytest.raises(assets.AssetError,match='bounded format/privacy') as error:
        assets.validate_asset(path)
    assert 'alice' not in str(error.value)


def test_compressed_output_is_bounded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(assets,'MAX_TEXT',100)
    path=tmp_path/'fixture.txt.gz';path.write_bytes(gzip.compress(b'x'*101))
    with pytest.raises(assets.AssetError):assets.validate_asset(path)


def test_image_pixel_budget_and_metadata(tmp_path: Path, monkeypatch) -> None:
    from PIL.PngImagePlugin import PngInfo
    path=tmp_path/'fixture.png';info=PngInfo();info.add_text('private','/Users/alice/secret')
    Image.new('RGB',(10,10)).save(path,pnginfo=info)
    with pytest.raises(assets.AssetError):assets.validate_asset(path)
    Image.new('RGB',(10,10)).save(path)
    monkeypatch.setattr(assets,'MAX_PIXELS',99)
    with pytest.raises(assets.AssetError):assets.validate_asset(path)


@pytest.mark.parametrize('damage',['script','metadata','stream','attachment'])
def test_pdf_active_and_hidden_content(tmp_path: Path, damage: str) -> None:
    writer=PdfWriter();writer.add_blank_page(72,72)
    if damage=='script':writer.add_js('app.alert(1)')
    elif damage=='metadata':writer.add_metadata({'/Title':'/Users/alice/hidden'})
    elif damage=='attachment':writer.add_attachment('extra.txt',b'extra')
    else:
        stream=DecodedStreamObject();stream.set_data(b'/Users/alice/hidden')
        writer._add_object(stream.flate_encode())  # Unreachable object still inspected.
    path=tmp_path/'fixture.pdf'
    with path.open('wb') as output:writer.write(output)
    with pytest.raises(assets.AssetError):assets.validate_asset(path)


@pytest.mark.parametrize('kind',['svg','css','json','png','pdf','txt.gz'])
def test_normal_assets_preserve_exact_bytes(tmp_path: Path, kind: str) -> None:
    picture=io.BytesIO();Image.new('RGB',(2,2)).save(picture,format='PNG')
    values={'svg':b'<svg xmlns="http://www.w3.org/2000/svg"><defs><style type="text/css">*{stroke-linejoin:round}</style><path id="p" d="M0 0"/></defs><use href="#p"/></svg>',
            'css':b'p { color: red; }','json':b'{"value":1}', 'png':picture.getvalue(),'pdf':generic_pdf('Public fixture'),'txt.gz':gzip.compress(b'Public text')}
    path=tmp_path/('fixture.'+kind);path.write_bytes(values[kind]);before=hashlib.sha256(path.read_bytes()).hexdigest()
    assets.validate_asset(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before


def test_theme_script_has_separate_trust_origin(tmp_path: Path) -> None:
    path=tmp_path/'theme.js';path.write_text('console.log("public")',encoding='utf-8')
    assets.validate_asset(path,origin='theme')
    with pytest.raises(assets.AssetError):assets.validate_asset(path)


def test_svg_admitted_relative_asset_reference(tmp_path: Path) -> None:
    path=tmp_path/'figure.svg';path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="image.png"/></svg>',encoding='utf-8')
    assets.validate_asset(path,relative='assets/figure.svg',approved=frozenset({'assets/image.png'}))


def test_matplotlib_style_svg_metadata_and_doctype(tmp_path: Path) -> None:
    path=tmp_path/'figure.svg'
    path.write_text('''<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" viewBox="0 0 10 10">
<metadata><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:Description><dc:title>Public figure</dc:title></rdf:Description></rdf:RDF></metadata>
<defs><style type="text/css">*{stroke-linejoin:round;stroke-linecap:butt}</style><path id="p" d="M0 0"/></defs><use xlink:href="#p"/>
</svg>''',encoding='utf-8')
    assets.validate_asset(path)


@pytest.mark.parametrize('damage',['filter','oversized','unknown-action'])
def test_pdf_unsupported_decoding_and_actions(tmp_path: Path, damage: str) -> None:
    writer=PdfWriter();writer.add_blank_page(72,72)
    if damage=='unknown-action':
        writer._root_object[NameObject('/OpenAction')]=DictionaryObject({NameObject('/S'):NameObject('/Unknown')})
    else:
        stream=DecodedStreamObject();stream.set_data(b'x'*(assets.MAX_TEXT+1) if damage=='oversized' else b'public')
        encoded=stream.flate_encode()
        if damage=='filter':encoded[NameObject('/Filter')]=NameObject('/JBIG2Decode')
        writer._add_object(encoded)
    path=tmp_path/'fixture.pdf'
    with path.open('wb') as output:writer.write(output)
    with pytest.raises(assets.AssetError):assets.validate_asset(path)

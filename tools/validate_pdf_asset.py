"""Disposable PDF inspector. Called with a bounded wall time by assets.py."""
from __future__ import annotations

import io
from pathlib import Path
import sys
from typing import Any

from pypdf import PdfReader, filters
from pypdf.generic import IndirectObject, StreamObject

from tools.site_assembly.assets import MAX_FILE, MAX_TEXT, inspect_strings
from tools.site_assembly.content_policy import URLUse, validate_url


class PDFPolicyError(ValueError):
    """A PDF exceeds the supported inert publication subset."""


def inspect_pdf(path: Path) -> None:
    # This process is disposable: parser limits/hooks never change parent state.
    for name in ('MAX_DECLARED_STREAM_LENGTH', 'MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH',
                 'LZW_MAX_OUTPUT_LENGTH', 'RUN_LENGTH_MAX_OUTPUT_LENGTH',
                 'ZLIB_MAX_OUTPUT_LENGTH', 'FLATE_MAX_BUFFER_SIZE'):
        setattr(filters, name, MAX_TEXT)
    original = filters.decode_stream_data
    total = 0
    allowed = {'/FlateDecode', '/Fl', '/ASCIIHexDecode', '/AHx', '/ASCII85Decode', '/A85', '/LZWDecode', '/LZW', '/RunLengthDecode', '/RL', '/DCTDecode', '/DCT'}
    def decode(stream: StreamObject) -> bytes:
        nonlocal total
        names = stream.get('/Filter', [])
        if isinstance(names, IndirectObject): names = names.get_object()
        if isinstance(names, str): names = [names]
        if not isinstance(names, list) or len(names) > 8 or any(str(name) not in allowed for name in names):
            raise PDFPolicyError('unsupported PDF stream filter')
        data = original(stream)
        total += len(data)
        if len(data) > MAX_TEXT or total > 4 * MAX_FILE:
            raise PDFPolicyError('PDF decoded stream limit exceeded')
        inspect_strings(data)
        return data
    filters.decode_stream_data = decode
    with path.open('rb') as stream: data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE: raise PDFPolicyError('PDF input limit exceeded')
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted or not 0 < len(reader.pages) <= 1000:
        raise PDFPolicyError('unsupported PDF encryption/page count')
    objects = [(number, generation) for generation, offsets in reader.xref.items() for number in offsets if number]
    objects += [(number, 0) for number in reader.xref_objStm]
    if len(objects) > 100_000: raise PDFPolicyError('PDF object limit exceeded')
    pending: list[tuple[Any, int, bool]] = [(reader.trailer, 0, False)]
    pending.extend((IndirectObject(number, generation, reader), 0, False) for number, generation in objects)
    seen: set[tuple[int, int, bool]] = set()
    count = 0
    forbidden = {'/AA', '/JS', '/JavaScript', '/Launch', '/EmbeddedFiles', '/EF', '/AF', '/AcroForm', '/RichMediaContent', '/XFA'}
    while pending:
        value, depth, action_context = pending.pop(); count += 1
        if count > 500_000 or depth > 64: raise PDFPolicyError('PDF structure limit exceeded')
        if isinstance(value, IndirectObject):
            identity = (value.idnum, value.generation, action_context)
            if identity in seen: continue
            seen.add(identity); pending.append((value.get_object(), depth + 1, action_context)); continue
        if isinstance(value, dict):
            if forbidden.intersection(value) or value.get('/Type') in {'/Filespec', '/EmbeddedFile'}:
                raise PDFPolicyError('active or attached PDF content')
            action = value.get('/S')
            if (action_context or value.get('/Type') == '/Action') and action not in {'/URI', '/GoTo'}:
                raise PDFPolicyError('unsupported PDF action context')
            if action is not None and action not in {'/URI', '/GoTo', '/D'}:
                # /S also names transparency group and structure semantics.
                if value.get('/Type') != '/Group' and '/S' in value and any(key in value for key in ('/Next', '/JS', '/F', '/URI', '/D')):
                    raise PDFPolicyError('unsupported PDF action')
            if action in {'/JavaScript', '/Launch', '/SubmitForm', '/ImportData', '/GoToR', '/GoToE', '/Rendition', '/Sound', '/Movie', '/Named', '/Hide', '/SetOCGState', '/ResetForm', '/Trans'}:
                raise PDFPolicyError('active PDF action')
            if '/URI' in value: validate_url(str(value['/URI']), URLUse.NAVIGATION)
            if isinstance(value, StreamObject):
                decoded = value.get_data()
                if len(decoded) > MAX_TEXT: raise PDFPolicyError('PDF stream limit exceeded')
                inspect_strings(decoded)
            pending.extend((item, depth + 1, False) for item in value.keys())
            pending.extend((item, depth + 1, key in {'/A', '/OpenAction', '/Next'}) for key, item in value.items())
        elif isinstance(value, list): pending.extend((item, depth + 1, False) for item in value)
        elif isinstance(value, (str, bytes)): inspect_strings(value)
    for page in reader.pages: inspect_strings(page.extract_text())


if __name__ == '__main__':
    try:
        inspect_pdf(Path(sys.argv[1]))
    except Exception:
        sys.exit(1)

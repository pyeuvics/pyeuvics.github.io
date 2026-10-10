"""Rewrite source URL spans identified by the actual Markdown renderer.

Python-Markdown does not expose source positions. Probe candidate spans with a
unique inert URL and ask its parsed output whether that span is a destination.
This retains original Markdown/code bytes and handles reference definitions,
HTML and extension syntax through the same parser used for validation. A final
render checks the complete destination multiset. No Markdown reserialization
or parallel Markdown grammar is maintained here.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from html import escape, unescape
import re


class LinkRewriteError(ValueError):
    """A destination cannot be mapped without changing unrelated source text."""


@dataclass(frozen=True)
class RenderedLinks:
    targets: tuple[str, ...]
    managed_targets: frozenset[str]


ESCAPE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);|\\[0-9a-fA-F]{1,6}[ \t\r\n\f]?|\\[!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~]")


def _normalized_source(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Map decoded entity, CSS escape and Markdown punctuation characters back to source spans."""
    result: list[str] = []
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in ESCAPE.finditer(text):
        for index in range(cursor, match.start()):
            result.append(text[index]); spans.append((index, index + 1))
        raw = match.group()
        if raw.startswith('\\') and re.fullmatch(r'[0-9a-fA-F]{1,6}\s?', raw[1:]):
            codepoint = int(raw[1:].strip(), 16)
            decoded = chr(codepoint) if 0 < codepoint <= 0x10ffff and not 0xd800 <= codepoint <= 0xdfff else '\ufffd'
        else:
            decoded = raw[1:] if raw.startswith('\\') else unescape(raw)
        result.extend(decoded)
        spans.extend([(match.start(), match.end())] * len(decoded))
        cursor = match.end()
    for index in range(cursor, len(text)):
        result.append(text[index]); spans.append((index, index + 1))
    return ''.join(result), spans


def rewrite_destinations(
    text: str,
    document: RenderedLinks,
    replacements: dict[str, tuple[str, str]],
    inspect: Callable[[str], RenderedLinks],
) -> str:
    """Replacement pairs are (Markdown destination, final raw-HTML URL)."""
    normalized, positions = _normalized_source(text)
    prefix = 'euvics-link-probe-' + sha256(text.encode('utf-8')).hexdigest() + '-'
    if prefix in text:
        raise LinkRewriteError('reserved link probe marker in source')
    edits: dict[tuple[int, int], str] = {}
    expected = Counter(document.targets)
    probes = 0
    for target, (managed, raw) in replacements.items():
        found = 0
        for match in re.finditer(re.escape(target), normalized):
            start, end = positions[match.start()][0], positions[match.end()-1][1]
            probes += 1
            if probes > 4096:
                raise LinkRewriteError('source exceeds the reviewed link-probe budget')
            marker = prefix + str(probes)
            parsed = inspect(text[:start] + marker + text[end:])
            count = parsed.targets.count(marker)
            if not count:
                continue
            replacement = managed if marker in parsed.managed_targets else raw
            if (start, end) in edits and edits[(start, end)] != escape(replacement, quote=True):
                raise LinkRewriteError('ambiguous overlapping source destinations')
            edits[(start, end)] = escape(replacement, quote=True)
            expected[target] -= count
            expected[replacement] += count
            found += count
        if found != document.targets.count(target):
            raise LinkRewriteError('unsupported or ambiguous source destination syntax')
    ordered = sorted(edits)
    if any(right[0] < left[1] for left, right in zip(ordered, ordered[1:])):
        raise LinkRewriteError('overlapping source destinations')
    rewritten = text
    for start, end in reversed(ordered):
        rewritten = rewritten[:start] + edits[(start, end)] + rewritten[end:]
    if Counter(inspect(rewritten).targets) != +expected:
        raise LinkRewriteError('rendered destinations changed unexpectedly during rewriting')
    return rewritten

"""Use MkDocs' validated Markdown settings at the publication boundary."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import markdown
from markdown.treeprocessors import Treeprocessor
from xml.etree.ElementTree import Element
from mkdocs.structure.files import File
from mkdocs.config import load_config
from mkdocs.exceptions import ConfigurationError

from .structured import StructuredInputError, read_yaml


class RenderingError(ValueError):
    """Website Markdown settings need an explicit compatibility review."""


# This is a compatibility gate, not a second renderer configuration. Rendering
# always uses the normalized values returned by MkDocs, including its defaults.
REVIEWED_SITE_EXTENSIONS: tuple[str | dict[str, dict[str, bool]], ...] = (
    "admonition", "attr_list", "md_in_html", "tables",
    {"pymdownx.arithmatex": {"generic": True}},
    "pymdownx.details", "pymdownx.superfences",
)
REVIEWED_EFFECTIVE_EXTENSIONS = (
    "toc", "tables", "fenced_code", "admonition", "attr_list", "md_in_html",
    "pymdownx.arithmatex", "pymdownx.details", "pymdownx.superfences",
)
REVIEWED_OPTIONS = (("pymdownx.arithmatex", (("generic", True),)),)


@dataclass(frozen=True)
class MarkdownRenderer:
    extensions: tuple[str, ...]
    options: tuple[tuple[str, tuple[tuple[str, bool], ...]], ...]

    def inspect(self, text: str) -> tuple[str, frozenset[str]]:
        engine = markdown.Markdown(
            extensions=list(self.extensions),
            extension_configs={name: dict(options) for name, options in self.options},
        )
        collector = _ManagedLinks(engine)
        engine.treeprocessors.register(collector, "publication_destinations", 0)
        return engine.convert(text), frozenset(collector.targets)

    def render(self, text: str) -> str:
        return self.inspect(text)[0]


class _ManagedLinks(Treeprocessor):
    """Record precisely the tree attributes MkDocs' relative-path pass rewrites."""

    def __init__(self, md: markdown.Markdown) -> None:
        super().__init__(md)
        self.targets: set[str] = set()

    def run(self, root: Element) -> None:
        for element in root.iter():
            key = {"a": "href", "img": "src"}.get(element.tag)
            if key is not None and (target := element.get(key)) is not None:
                self.targets.add(target)


def final_relative_url(target: Path, current: Path) -> str:
    """Use MkDocs' actual file-to-URL rules for attributes it does not rewrite."""
    target_file = File(target.as_posix().lstrip("/"), "", "", use_directory_urls=True)
    current_file = File(current.as_posix().lstrip("/"), "", "", use_directory_urls=True)
    return target_file.url_relative_to(current_file)


def load_renderer(website_root: Path | None = None) -> MarkdownRenderer:
    root = website_root if website_root is not None else Path(__file__).resolve().parents[2]
    path = root / "mkdocs.yml"
    try:
        raw = read_yaml(path)
    except StructuredInputError as exc:
        raise RenderingError("invalid website renderer configuration") from exc
    # Check before MkDocs imports any newly configured extension. JSON comparison
    # intentionally distinguishes true from 1 as well as preserving list order.
    if not isinstance(raw, dict) or json.dumps(raw.get("markdown_extensions"), sort_keys=True) != json.dumps(REVIEWED_SITE_EXTENSIONS, sort_keys=True):
        raise RenderingError("website Markdown settings require compatibility review")
    if raw.get("use_directory_urls") is not True:
        raise RenderingError("directory URL policy requires compatibility review")
    try:
        config = load_config(config_file=str(path))
    except ConfigurationError as exc:
        raise RenderingError("invalid MkDocs configuration") from exc
    extensions = tuple(config.markdown_extensions)
    settings = config.mdx_configs or {}
    if extensions != REVIEWED_EFFECTIVE_EXTENSIONS or json.dumps(settings, sort_keys=True) != json.dumps({name: dict(options) for name, options in REVIEWED_OPTIONS}, sort_keys=True):
        raise RenderingError("effective MkDocs Markdown settings require compatibility review")
    options = tuple((name, tuple(values.items())) for name, values in settings.items())
    return MarkdownRenderer(extensions, options)

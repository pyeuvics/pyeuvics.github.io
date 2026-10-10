"""Shared notebook admission/output policy and typed phase results."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, TYPE_CHECKING
from tools.privacy import PrivacyError, ScanProfile, scan_text
from .content_policy import ContentPolicyError, parse_fragment
from .rendering import RenderingError, load_renderer
from .models import NotebookSpec
if TYPE_CHECKING:
    from .notebook_environment import EnvironmentIdentity

DATA_LITERAL = re.compile(
    r"[\"']([^\"']+\.(?:csv|json|ya?ml|npy|npz|h5|hdf5|parquet|dat|txt))[\"']",
    re.IGNORECASE,
)
NETWORK_CODE = re.compile(r"\b(?:requests\.|httpx\.|urlopen\s*\(|socket\.|wget\b|curl\b)")
UNSAFE_HTML = re.compile(r"<(?:script|iframe)\b|javascript:", re.IGNORECASE)
SAFE_OUTPUT_MIMES = {"text/plain", "text/markdown", "image/png", "image/jpeg"}
INHERITED_ENVIRONMENT = {
    "CONDA_PREFIX", "PATH", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR",
    "VIRTUAL_ENV", "WINDIR",
}


class NotebookError(ValueError):
    """An approved notebook cannot be safely rendered."""


def _scan(value: str, label: str) -> None:
    try:
        scan_text(value, label, ScanProfile.NOTEBOOK)
    except PrivacyError as exc:
        raise NotebookError(str(exc)) from exc


def _validate_markup(text: str, label: str) -> None:
    try:
        parse_fragment(load_renderer().render(text))
    except (ContentPolicyError, RenderingError) as exc:
        raise NotebookError(f"unsafe active content in {label}: {exc}") from exc



@dataclass(frozen=True)
class AdmittedNotebook:
    spec: NotebookSpec
    source_root: Path
    notebook: Any


@dataclass(frozen=True)
class ExecutedNotebook:
    spec: NotebookSpec
    notebook: Any
    environment: EnvironmentIdentity | None = None


@dataclass(frozen=True)
class RenderedNotebook:
    body: str
    assets: dict[str, bytes]
    environment: EnvironmentIdentity | None = None

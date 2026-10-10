"""Immutable inputs and stage locations for one publication build."""
from dataclasses import dataclass
from pathlib import Path

from .models import SourceContract
from .rendering import MarkdownRenderer
from .staging import StagingPlan
from .timestamps import BuildTimestamp


@dataclass(frozen=True)
class BuildInputs:
    website_root: Path
    requested_output: Path
    timestamp: BuildTimestamp
    contracts: tuple[SourceContract, ...]
    plan: StagingPlan
    renderer: MarkdownRenderer


@dataclass(frozen=True)
class BuildContext:
    inputs: BuildInputs
    workspace: Path

    @property
    def content(self) -> Path:
        return self.workspace / 'content'

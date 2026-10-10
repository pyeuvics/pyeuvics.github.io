"""Versioned typed review artifact records and pure complete comparisons."""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from .site_assembly.primitives import atomic_write_text
from .site_assembly.staging import portable_path
from .site_assembly.structured import read_json


class ReviewManifestError(ValueError):
    """Review metadata is malformed, ambiguous or outside the versioned contract."""

@dataclass(frozen=True)
class ReviewFile:
    path: str
    sha256: str
    bytes: int

@dataclass(frozen=True)
class ReviewManifest:
    files: tuple[ReviewFile,...]

    def to_dict(self) -> dict[str,object]:
        return {'manifest_version':1,'files':[asdict(item) for item in self.files]}

    def by_path(self) -> dict[str,ReviewFile]:
        return {item.path:item for item in self.files}

@dataclass(frozen=True)
class ArtifactComparison:
    added: tuple[str,...]
    removed: tuple[str,...]
    changed: tuple[str,...]
    baseline_files: int
    candidate_files: int

    def to_dict(self) -> dict[str,object]:
        return {'comparison_version':1,**asdict(self)}


def parse_review_manifest(raw: object) -> ReviewManifest:
    try:
        if not isinstance(raw,dict) or set(raw)!={'manifest_version','files'} or type(raw['manifest_version']) is not int or raw['manifest_version']!=1 or not isinstance(raw['files'],list) or len(raw['files'])>100000:
            raise ReviewManifestError('invalid review artifact manifest shape or version')
        records=[];identities=set();paths=[]
        for item in raw['files']:
            if not isinstance(item,dict) or set(item)!={'path','sha256','bytes'}:
                raise ReviewManifestError('invalid review artifact entry shape')
            path,digest,size=item['path'],item['sha256'],item['bytes']
            if not isinstance(path,str) or unicodedata.normalize('NFC',path)!=path or any(unicodedata.category(char) in {'Cc','Cf'} for char in path):
                raise ReviewManifestError('noncanonical review artifact path')
            identity=portable_path(path)
            if identity in identities:raise ReviewManifestError('duplicate review artifact path')
            if not isinstance(digest,str) or re.fullmatch('[0-9a-f]{64}',digest) is None or type(size) is not int or size<0:
                raise ReviewManifestError('invalid review artifact digest or byte count')
            identities.add(identity);paths.append(path);records.append(ReviewFile(path,digest,size))
        if paths!=sorted(paths):raise ReviewManifestError('review artifact paths are not in deterministic order')
        return ReviewManifest(tuple(records))
    except ReviewManifestError:raise
    except (ValueError,TypeError,KeyError,RecursionError) as exc:
        raise ReviewManifestError('invalid review artifact manifest') from exc


def read_review_manifest(path: Path) -> ReviewManifest:
    try:
        if path.stat().st_size>16*1024*1024:raise ReviewManifestError('review manifest exceeds size limit')
        return parse_review_manifest(read_json(path))
    except (OSError,ValueError,RecursionError) as exc:
        raise ReviewManifestError('cannot read valid review artifact manifest') from exc


def write_manifest(path: Path,manifest: ReviewManifest) -> None:
    checked=parse_review_manifest(manifest.to_dict())
    atomic_write_text(path,json.dumps(checked.to_dict(),indent=2,sort_keys=True)+'\n')


def compare_artifacts(baseline: ReviewManifest,candidate: ReviewManifest) -> ArtifactComparison:
    before=baseline.by_path();after=candidate.by_path()
    return ArtifactComparison(tuple(sorted(after.keys()-before.keys())),tuple(sorted(before.keys()-after.keys())),tuple(sorted(path for path in after.keys()&before.keys() if after[path]!=before[path])),len(before),len(after))

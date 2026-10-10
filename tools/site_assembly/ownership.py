"""Reconcile staged/final publication files against declared producers and paths."""
from __future__ import annotations

import base64
import json
import stat
from dataclasses import asdict, dataclass
from importlib.metadata import distribution
from pathlib import Path, PurePosixPath
from typing import Literal

from mkdocs.config import load_config
from mkdocs.structure.files import InclusionLevel, get_files

from .context import BuildContext
from .models import InventoryEntry
from .primitives import atomic_write_text, sha256_file
from .staging import DestinationRegistry, OutputKind, PlannedOutput
from .structured import read_json
from .website_inputs import website_inputs


class OwnershipError(ValueError):
    """A produced file is missing, unexpected, aliased or differs from its owner."""


@dataclass(frozen=True)
class StagedFile:
    path: str
    owner: str
    producer: str
    sha256: str


@dataclass(frozen=True)
class ArtifactFile:
    path: str
    owner: str
    producer: str
    origin: Literal['website', 'source', 'theme']
    input_path: str
    input_sha256: str
    expected_sha256: str | None


@dataclass(frozen=True)
class ArtifactPlan:
    staged: tuple[StagedFile, ...]
    files: tuple[ArtifactFile, ...]

    def to_dict(self) -> dict[str, object]:
        return {'artifact_plan_version': 1, 'staged': [asdict(item) for item in self.staged], 'files': [asdict(item) for item in self.files]}


@dataclass(frozen=True)
class RenderedBuild:
    site: Path
    plan: ArtifactPlan


def _tree_files(root: Path, expected: set[str], namespaces: set[str] | None = None) -> None:
    if not root.is_dir() or root.is_symlink():
        raise OwnershipError('publication tree is missing or aliased')
    directories = {parent.as_posix() for name in expected for parent in PurePosixPath(name).parents if parent.as_posix() != '.'}
    directories.update(namespaces or set())
    actual: set[str] = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise OwnershipError(f'symlink in produced publication tree: {relative}')
        if stat.S_ISREG(mode):
            actual.add(relative)
        elif stat.S_ISDIR(mode):
            if relative not in directories:
                raise OwnershipError(f'unowned publication directory: {relative}')
        else:
            raise OwnershipError(f'non-regular publication output: {relative}')
    if actual != expected:
        raise OwnershipError(f'publication ownership mismatch: extra={sorted(actual-expected)}, missing={sorted(expected-actual)}')


def stage_receipt(context: BuildContext, entries: tuple[InventoryEntry, ...]) -> tuple[StagedFile, ...]:
    plan = context.inputs.plan
    expected = {item.path: item for item in plan.outputs}
    bindings = {(item.source, item.source_path): item.output_path for item in plan.destinations}
    inputs = {item.identity: item for item in plan.inputs}
    seen: set[tuple[str, str]] = set()
    dynamic: dict[str, list[str]] = {}
    for entry in entries:
        key = (entry.source, entry.source_path)
        if key in seen:
            raise OwnershipError('duplicate producer inventory entry')
        seen.add(key)
        if key in bindings:
            if entry.staged_path != bindings[key] or entry.source_sha256 != inputs[f'{entry.source}:{entry.source_path}'].sha256:
                raise OwnershipError('producer inventory does not match planned source binding')
        else:
            notebook, separator, asset = entry.source_path.partition('#output:')
            if not separator or not asset or (entry.source, notebook) not in bindings:
                raise OwnershipError('unplanned producer inventory entry')
            page = PurePosixPath(bindings[(entry.source, notebook)])
            if entry.staged_path != (page.parent / asset).as_posix() or entry.source_sha256 != entry.staged_sha256:
                raise OwnershipError('notebook asset inventory does not match its producer')
            dynamic.setdefault(entry.source, []).append(entry.staged_path)
        if sha256_file(context.content / entry.staged_path) != entry.staged_sha256:
            raise OwnershipError(f'staged producer checksum mismatch: {entry.staged_path}')
    if not bindings.keys() <= seen:
        raise OwnershipError('producer inventory is missing planned source outputs')
    for owner, paths in dynamic.items():
        for item in plan.emitted_assets(owner, tuple(paths)):
            if item.path in expected:
                raise OwnershipError('dynamic output collides with a fixed producer')
            expected[item.path] = item
    _tree_files(context.content, set(expected), {item.path for item in plan.namespaces})
    by_output = {item.output_path:item for item in plan.destinations}
    for item in expected.values():
        source_digest: str | None = None
        if item.producer == 'website-copy':
            source_digest = inputs[item.inputs[0]].sha256
        elif item.producer in {'asset-import', 'document-build'}:
            binding = by_output[item.path]
            source_digest = inputs[f'{binding.source}:{binding.source_path}'].sha256
        if source_digest is not None and sha256_file(context.content/item.path) != source_digest:
            raise OwnershipError(f'staged copied input checksum mismatch: {item.path}')
    inventory = context.workspace / 'staged-content-inventory.json'
    if inventory.read_bytes() != (context.content/'imported/staged-content-inventory.json').read_bytes():
        raise OwnershipError('public inventory differs from its producer receipt')
    payload = read_json(inventory)
    expected_inventory = {
        'inventory_version':1, 'build_timestamp':context.inputs.timestamp.iso,
        'sources':{contract.lock.name:{'repository':contract.lock.repository,'commit':contract.lock.commit,'publication_manifest':contract.lock.manifest_path} for contract in context.inputs.contracts},
        'files':[dict(asdict(item),known_limitations=list(item.known_limitations)) for item in entries],
    }
    if payload != expected_inventory:
        raise OwnershipError('inventory bytes differ from the admitted producer entries')
    return tuple(StagedFile(path,item.owner,item.producer,sha256_file(context.content/path)) for path,item in sorted(expected.items()))


class ThemeInputs:
    def __init__(self, context: BuildContext) -> None:
        self.context = context
        self.inputs = {item.identity: item for item in context.inputs.plan.inputs}
        self.distributions = [(name, distribution(name)) for name in ('mkdocs','mkdocs-material')]
        self.records = {name:{str(item):item for item in dist.files or ()} for name,dist in self.distributions}

    def inspect(self, path: Path) -> tuple[str, str, Literal['website','theme']]:
        if path.is_symlink() or not path.is_file():
            raise OwnershipError('theme input is missing or aliased')
        digest = sha256_file(path)
        overrides = self.context.workspace/'overrides'
        if path.is_relative_to(overrides):
            identity = 'website:overrides/'+path.relative_to(overrides).as_posix()
            if identity not in self.inputs or digest != self.inputs[identity].sha256:
                raise OwnershipError('unowned or changed website override')
            return identity,digest,'website'
        for name,dist in self.distributions:
            base = Path(str(dist.locate_file(''))).resolve()
            if not path.is_relative_to(base):
                continue
            relative = path.relative_to(base).as_posix()
            record = self.records[name].get(relative)
            if record is None:
                continue
            encoded = base64.urlsafe_b64encode(bytes.fromhex(digest)).decode('ascii').rstrip('=')
            if record.hash is None or record.hash.mode != 'sha256' or record.hash.value != encoded:
                raise OwnershipError('trusted theme input differs from its installed package record')
            return f'{name}@{dist.version}:{relative}',digest,'theme'
        raise OwnershipError('theme input is outside declared website/package ownership')


def plan_artifact(context: BuildContext, staged: tuple[StagedFile, ...]) -> ArtifactPlan:
    config = load_config(str(context.workspace/'mkdocs.yml'))
    if set(config.plugins) != {'material/search'} or config.extra_templates or config.theme.name != 'material':
        raise OwnershipError('website output producers require compatibility review')
    config = config.plugins.on_config(config)
    if config.theme.static_templates != {'404.html','sitemap.xml'}:
        raise OwnershipError('theme template outputs require compatibility review')
    files = get_files(config)
    by_path = {item.path:item for item in staged}
    if {item.src_uri for item in files if item.inclusion not in {InclusionLevel.EXCLUDED, InclusionLevel.DRAFT}} != set(by_path):
        raise OwnershipError('MkDocs excludes or adds a planned staged file')
    environment = config.theme.get_env()
    files.add_files_from_theme(environment,config)
    trusted = ThemeInputs(context)
    registry = DestinationRegistry()
    outputs: list[ArtifactFile] = []
    def add(item: ArtifactFile) -> None:
        registry.add(PlannedOutput(item.path,item.owner,item.producer,OutputKind.GENERATED))
        outputs.append(item)
    for file in files:
        if file.src_uri in by_path:
            source = by_path[file.src_uri]
            add(ArtifactFile(file.dest_uri,source.owner,'mkdocs-page' if file.is_documentation_page() else source.producer,'website' if source.owner=='website' else 'source',file.src_uri,source.sha256,None if file.is_documentation_page() else source.sha256))
        else:
            if file.abs_src_path is None:
                raise OwnershipError('theme file lacks an owned source')
            identity,digest,origin = trusted.inspect(Path(file.abs_src_path))
            add(ArtifactFile(file.dest_uri,'website','theme-copy',origin,identity,digest,digest))
    for name in sorted(config.theme.static_templates):
        template = environment.get_template(name)
        if template.filename is None:
            raise OwnershipError('static template lacks an owned input')
        identity,digest,origin = trusted.inspect(Path(template.filename))
        add(ArtifactFile(name,'website','theme-template',origin,identity,digest,None))
    sitemap = next(item for item in outputs if item.path=='sitemap.xml')
    add(ArtifactFile('sitemap.xml.gz','website','mkdocs-gzip','theme',sitemap.input_path,sitemap.input_sha256,None))
    add(ArtifactFile('search/search_index.json','website','material-search','theme','material/search',sha256_file(context.workspace/'staging-plan.json'),None))
    plan = ArtifactPlan(staged,tuple(sorted(outputs,key=lambda item:item.path)))
    atomic_write_text(context.workspace/'artifact-plan.json',json.dumps(plan.to_dict(),indent=2,sort_keys=True)+'\n')
    return plan


def verify_ownership(context: BuildContext, rendered: RenderedBuild) -> None:
    if set(website_inputs(context.inputs.website_root)) != {item.path for item in context.inputs.plan.inputs if item.source == 'website'}:
        raise OwnershipError('website input ownership changed during assembly')
    expected_plan = json.dumps(context.inputs.plan.to_dict(),indent=2,sort_keys=True)+'\n'
    if (context.workspace/'staging-plan.json').read_text(encoding='utf-8') != expected_plan:
        raise OwnershipError('staging plan changed during rendering')
    _tree_files(context.content,{item.path for item in rendered.plan.staged},{item.path for item in context.inputs.plan.namespaces})
    for item in rendered.plan.staged:
        if sha256_file(context.content/item.path) != item.sha256:
            raise OwnershipError(f'staged file changed during rendering: {item.path}')
    for input_item in context.inputs.plan.inputs:
        if input_item.source=='website' and sha256_file(context.inputs.website_root/input_item.path) != input_item.sha256:
            raise OwnershipError(f'website input changed during assembly: {input_item.path}')
    _tree_files(rendered.site,{item.path for item in rendered.plan.files})
    records: list[dict[str, object]] = []
    for artifact_item in rendered.plan.files:
        digest = sha256_file(rendered.site/artifact_item.path)
        if artifact_item.expected_sha256 is not None and digest != artifact_item.expected_sha256:
            raise OwnershipError(f'final copied output checksum mismatch: {artifact_item.path}')
        records.append(dict(asdict(artifact_item),sha256=digest,bytes=(rendered.site/artifact_item.path).stat().st_size))
    atomic_write_text(context.workspace/'publication-artifact-manifest.json',json.dumps({'ownership_version':1,'staging_plan_sha256':sha256_file(context.workspace/'staging-plan.json'),'files':records},indent=2,sort_keys=True)+'\n')

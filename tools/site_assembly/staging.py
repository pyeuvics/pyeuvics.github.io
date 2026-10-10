"""Deterministic publication outputs and portable destination ownership."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path, PurePosixPath
import re
import unicodedata

from .documents import DocumentError, _validate_document_entry
from .models import SourceContract
from .primitives import FileOperationError, sha256_file
from .website_inputs import website_inputs


class StagingError(ValueError):
    """The publication output graph is ambiguous or cannot be constructed."""


class OutputKind(Enum):
    WEBSITE = 'website input'
    IMPORT = 'source import'
    DOCUMENT = 'approved PDF'
    RENDERED = 'rendered source page'
    GENERATED = 'website generated page'
    PROVENANCE = 'generated provenance'


@dataclass(frozen=True)
class InputBytes:
    identity: str
    source: str
    path: str
    sha256: str
    repository: str | None = None
    commit: str | None = None


@dataclass(frozen=True)
class PlannedOutput:
    path: str
    owner: str
    producer: str
    kind: OutputKind
    inputs: tuple[str, ...] = ()
    related_outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutputNamespace:
    path: str
    owner: str
    producer: str
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class SourceDestination:
    source: str
    source_path: str
    output_path: str


@dataclass(frozen=True)
class StagingPlan:
    inputs: tuple[InputBytes, ...]
    outputs: tuple[PlannedOutput, ...]
    namespaces: tuple[OutputNamespace, ...]
    destinations: tuple[SourceDestination, ...]

    def source_destinations(self, source: str, content: Path) -> dict[str, Path]:
        return {item.source_path: content / item.output_path for item in self.destinations if item.source == source}

    def output(self, path: str) -> PlannedOutput:
        for item in self.outputs:
            if item.path == path:
                return item
        raise StagingError(f'output is not planned: {path}')

    def emitted_assets(self, owner: str, paths: tuple[str, ...]) -> tuple[PlannedOutput, ...]:
        registry = DestinationRegistry()
        result: list[PlannedOutput] = []
        for path in sorted(paths):
            portable_path(path)
            matches = [item for item in self.namespaces if item.owner == owner and PurePosixPath(item.path) in PurePosixPath(path).parents]
            if len(matches) != 1:
                raise StagingError(f"generated asset is outside its owned namespace: {path}")
            namespace = matches[0]
            output = PlannedOutput(path, owner, namespace.producer, OutputKind.RENDERED, namespace.inputs)
            registry.add(output)
            result.append(output)
        return tuple(result)

    def to_dict(self) -> dict[str, object]:
        return {
            'plan_version': 1,
            'inputs': [asdict(item) for item in self.inputs],
            'outputs': [dict(asdict(item), kind=item.kind.value) for item in self.outputs],
            'namespaces': [asdict(item) for item in self.namespaces],
            'destinations': [asdict(item) for item in self.destinations],
        }


RESERVED_DEVICE = re.compile(r'^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', re.I)


def portable_path(value: str) -> tuple[str, ...]:
    path = PurePosixPath(value)
    if not value or not path.parts or path.is_absolute() or path.as_posix() != value or any(
        part in {'.', '..'} or part.endswith(('.', ' ')) or RESERVED_DEVICE.match(part)
        for part in path.parts
    ) or any(char in value for char in '\\:<>"|?*') or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise StagingError(f'output path is not portable and relative: {value}')
    return tuple(unicodedata.normalize('NFC', part).casefold() for part in path.parts)


class DestinationRegistry:
    def __init__(self) -> None:
        self.outputs: dict[str, PlannedOutput] = {}
        self.namespaces: dict[str, OutputNamespace] = {}
        self._spellings: dict[tuple[str, ...], str] = {}
        self._files: set[tuple[str, ...]] = set()
        self._directories: set[tuple[str, ...]] = set()
        self._reserved: set[tuple[str, ...]] = set()

    def _claim(self, path: str, *, namespace: bool = False) -> None:
        key = portable_path(path)
        parts = PurePosixPath(path).parts
        for index in range(1, len(key) + 1):
            prefix = key[:index]
            spelling = '/'.join(parts[:index])
            if prefix in self._spellings and self._spellings[prefix] != spelling:
                raise StagingError(f'portable case or Unicode alias in output: {path}')
            if prefix in self._files or prefix in self._reserved:
                raise StagingError(f'duplicate destination or file/directory conflict: {path}')
        if key in self._directories:
            raise StagingError(f'file/directory or namespace conflict: {path}')
        for index in range(1, len(key) + 1):
            self._spellings[key[:index]] = '/'.join(parts[:index])
        self._directories.update(key[:index] for index in range(1, len(key)))
        (self._reserved if namespace else self._files).add(key)

    def add(self, output: PlannedOutput) -> None:
        if output.owner not in {"website", "euvics", "pyeuvics"} or not output.producer.strip():
            raise StagingError("output must have one reviewed owner and producer")
        self._claim(output.path)
        self.outputs[output.path] = output

    def reserve(self, namespace: OutputNamespace) -> None:
        if namespace.owner not in {"website", "euvics", "pyeuvics"} or not namespace.producer.strip():
            raise StagingError("namespace must have one reviewed owner and producer")
        self._claim(namespace.path, namespace=True)
        self.namespaces[namespace.path] = namespace


def notebook_page(path: str) -> str:
    return f'software/notebooks/{PurePosixPath(path).stem}.md'


def notebook_assets(path: str) -> str:
    return f'software/notebooks/{PurePosixPath(path).stem}_files'


def create_staging_plan(website_root: Path, contracts: tuple[SourceContract, ...]) -> StagingPlan:
    """Declare all fixed staged outputs and exclusive dynamic notebook namespaces."""
    if len({item.lock.name for item in contracts}) != len(contracts):
        raise StagingError("duplicate source identity in staging plan")
    registry = DestinationRegistry()
    inputs: dict[str, InputBytes] = {}
    website_paths = website_inputs(website_root)
    for path in website_paths:
        identity = f"website:{path}"
        inputs[identity] = InputBytes(identity, "website", path, sha256_file(website_root / path))
    bindings: list[SourceDestination] = []
    generated: dict[str, PlannedOutput] = {}
    all_source_inputs: list[str] = []
    for contract in sorted(contracts, key=lambda item: item.lock.name):
        paths = {item.path for item in contract.files} | {contract.lock.manifest_path}
        if contract.lock.name == 'pyeuvics':
            paths.add('CITATION.cff')
        for spec in contract.notebooks:
            paths.update((spec.path, *spec.dependencies, *spec.configurations))
        for relative in sorted(paths):
            identity = f'{contract.lock.name}:{relative}'
            inputs[identity] = InputBytes(identity, contract.lock.name, relative, sha256_file(contract.root / relative), contract.lock.repository, contract.lock.commit)
            all_source_inputs.append(identity)
        manifest = f'{contract.lock.name}:{contract.lock.manifest_path}'
        for item in contract.files:
            dependencies: tuple[str, ...] = (manifest, f'{contract.lock.name}:{item.path}', 'website:mkdocs.yml')
            if item.kind == 'pdf':
                try:
                    _, overview, output = _validate_document_entry(item)
                except DocumentError as exc:
                    raise StagingError(str(exc)) from exc
                registry.add(PlannedOutput(output, contract.lock.name, 'document-build', OutputKind.DOCUMENT, dependencies, (overview,)))
                generated[overview] = PlannedOutput(overview, 'website', 'document-overview', OutputKind.GENERATED, dependencies, (output,))
            else:
                output = f'imported/{contract.lock.name}/{item.path}'
                registry.add(PlannedOutput(output, contract.lock.name, 'markdown-import' if PurePosixPath(item.path).suffix.lower() == '.md' else 'asset-import', OutputKind.IMPORT, dependencies))
            bindings.append(SourceDestination(contract.lock.name, item.path, output))
        for spec in contract.notebooks:
            dependencies = (manifest, *(f'{contract.lock.name}:{path}' for path in sorted({spec.path, *spec.dependencies, *spec.configurations})))
            output = notebook_page(spec.path)
            registry.add(PlannedOutput(output, contract.lock.name, 'notebook-render', OutputKind.RENDERED, dependencies, (notebook_assets(spec.path),)))
            registry.reserve(OutputNamespace(notebook_assets(spec.path), contract.lock.name, 'notebook-assets', dependencies))
            bindings.append(SourceDestination(contract.lock.name, spec.path, output))
        if contract.notebooks:
            generated['software/notebooks/index.md'] = PlannedOutput('software/notebooks/index.md', 'website', 'notebook-index', OutputKind.GENERATED, (manifest,), tuple(notebook_page(spec.path) for spec in contract.notebooks))
        if contract.lock.name == 'pyeuvics':
            for prefix, page in [('reference_6p7nm', '6-7-nm'), ('reference_13p5nm', '13-5-nm')]:
                selected = tuple(f'{contract.lock.name}:{item.path}' for item in contract.files if item.path.startswith(f'campaigns/{prefix}/'))
                if selected:
                    output = f'campaigns/{page}.md'
                    generated[output] = PlannedOutput(output, 'website', 'campaign-overview', OutputKind.GENERATED, (manifest, *selected))
    source_inputs = tuple(sorted(all_source_inputs))
    for output in ('index.md', 'project/overview.md', 'software/installation.md', 'software/science.md', 'software/api.md', 'software/tutorials.md', 'software/workflows.md', 'software/validation.md'):
        generated[output] = PlannedOutput(output, 'website', 'entry-page', OutputKind.GENERATED, source_inputs)
    registry.add(PlannedOutput('imported/staged-content-inventory.json', 'website', 'inventory', OutputKind.PROVENANCE, source_inputs))
    try:
        for path in website_paths:
            if not path.startswith('content/'):
                continue
            relative = PurePosixPath(path).relative_to('content').as_posix()
            identity = f'website:{path}'
            if relative in generated:
                output_record = generated.pop(relative)
                registry.add(replace(output_record, inputs=(identity, *output_record.inputs)))
            else:
                registry.add(PlannedOutput(relative, 'website', 'website-copy', OutputKind.WEBSITE, (identity,)))
    except (FileOperationError, OSError, ValueError) as exc:
        raise StagingError(f'cannot plan website content: {exc}') from exc
    for output_record in generated.values():
        registry.add(output_record)
    claims: tuple[PlannedOutput | OutputNamespace, ...] = (*registry.outputs.values(), *registry.namespaces.values())
    for claim in claims:
        if set(claim.inputs) - inputs.keys():
            raise StagingError('output has an unregistered input')
    known_outputs = registry.outputs.keys() | registry.namespaces.keys()
    if any(set(item.related_outputs) - known_outputs for item in registry.outputs.values()):
        raise StagingError('output has an unregistered relationship')
    if len({(item.source, item.source_path) for item in bindings}) != len(bindings):
        raise StagingError('ambiguous source-to-output binding')
    return StagingPlan(tuple(inputs[key] for key in sorted(inputs)), tuple(registry.outputs[key] for key in sorted(registry.outputs)), tuple(registry.namespaces[key] for key in sorted(registry.namespaces)), tuple(sorted(bindings, key=lambda item: (item.source, item.source_path))))

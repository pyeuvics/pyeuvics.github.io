"""Typed structural validation of the already reviewed overview case; no physics."""
from __future__ import annotations

import csv
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import Version

from .assets import MAX_TEXT, validate_asset
from .models import SourceContract
from .structured import finite_number, read_json

FIGURE_ROOT='docs/generated/overview-figures'
SVG_PATH=f'{FIGURE_ROOT}/kinetic-energy-scan.svg'
CSV_PATH=f'{FIGURE_ROOT}/kinetic-energy-scan.csv'
JSON_PATH=f'{FIGURE_ROOT}/kinetic-energy-scan.json'
EXPECTED_PATHS={SVG_PATH,CSV_PATH,JSON_PATH}
SVG_NS='{http://www.w3.org/2000/svg}'


class OverviewFigureError(ValueError):
    """An overview set differs from its reviewed structural contract."""


@dataclass(frozen=True)
class ScanGrid:
    minimum: float
    maximum: float
    point_count: int


@dataclass(frozen=True)
class FigureDescriptor:
    package_version: str
    generator_commit: str
    grid: ScanGrid
    limitations: tuple[str,...]


@dataclass(frozen=True)
class FigureTable:
    energies: tuple[float,...]
    wavelengths: tuple[float,...]


@dataclass(frozen=True)
class OverviewArtifacts:
    descriptor: FigureDescriptor
    table: FigureTable


def _reviewed_value(actual: Any, expected: Any) -> bool:
    if type(expected) is float:
        return finite_number(actual,'overview setting')==expected
    if isinstance(expected,dict):
        return isinstance(actual,dict) and set(actual)==set(expected) and all(_reviewed_value(actual[key],value) for key,value in expected.items())
    return type(actual) is type(expected) and actual==expected


def _descriptor(path: Path,version: str) -> FigureDescriptor:
    if path.stat().st_size>MAX_TEXT:raise OverviewFigureError('overview descriptor exceeds size limit')
    metadata=read_json(path)
    if not isinstance(metadata,dict):raise OverviewFigureError('overview descriptor must be an object')
    package=metadata.get('package');model=metadata.get('model')
    if not isinstance(package,dict) or package.get('name')!='pyEUVICS' or not isinstance(model,dict):
        raise OverviewFigureError('overview package/model identity is invalid')
    package_version=package.get('version');commit=package.get('source_commit')
    if not isinstance(package_version,str) or not package_version or package_version!=version:
        raise OverviewFigureError('overview package version is missing or inconsistent')
    Version(package_version)
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):
        raise OverviewFigureError('overview generator commit is invalid')
    if metadata.get('artifact_status')!='calculated-unvalidated' or metadata.get('calculation_entry_point')!='examples/generate_overview_energy_scan.py':
        raise OverviewFigureError('overview status or calculation entry point is inconsistent')
    files=metadata.get('files')
    if not isinstance(files,list) or len(files)!=2 or any(not isinstance(item,str) for item in files) or set(files)!={Path(CSV_PATH).name,Path(SVG_PATH).name}:
        raise OverviewFigureError('overview declared artifact files are inconsistent')
    policy=read_json(Path(__file__).with_name('overview-model-v1.json'))
    if not isinstance(policy,dict) or type(policy.get('policy_version')) is not int or policy['policy_version']!=1 or not _reviewed_value(model,policy.get('model')):
        raise OverviewFigureError('overview model settings differ from the reviewed case')
    limitations=metadata.get('limitations')
    if not isinstance(limitations,list) or len(limitations)<3 or any(not isinstance(item,str) or not item.strip() for item in limitations):
        raise OverviewFigureError('overview limitations are incomplete')
    grid=model['electron_kinetic_energy_MeV']
    return FigureDescriptor(package_version,commit,ScanGrid(finite_number(grid['minimum'],'grid minimum',positive=True),finite_number(grid['maximum'],'grid maximum',positive=True),grid['point_count']),tuple(limitations))


def _table(path: Path,grid: ScanGrid) -> FigureTable:
    if path.stat().st_size>MAX_TEXT:raise OverviewFigureError('overview table exceeds size limit')
    energies: list[float]=[]
    wavelengths: list[float]=[]
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['electron_kinetic_energy_MeV','scattered_wavelength_nm']:
            raise OverviewFigureError('overview CSV headers differ from the reviewed columns')
        for row in reader:
            if len(energies)>=grid.point_count or None in row or any(value is None for value in row.values()):
                raise OverviewFigureError('overview CSV shape/count is invalid')
            energies.append(finite_number(float(row['electron_kinetic_energy_MeV']),'kinetic energy',positive=True))
            wavelengths.append(finite_number(float(row['scattered_wavelength_nm']),'wavelength',positive=True))
    if len(energies)!=grid.point_count:raise OverviewFigureError('overview point count is inconsistent')
    for index,value in enumerate(energies):
        expected=grid.minimum+(grid.maximum-grid.minimum)*index/(grid.point_count-1)
        if not math.isclose(value,expected,rel_tol=0,abs_tol=1e-12):
            raise OverviewFigureError('overview kinetic-energy grid differs from the reviewed scan')
    if any(later>=earlier for earlier,later in zip(wavelengths,wavelengths[1:])):
        raise OverviewFigureError('overview wavelength trend is not strictly decreasing')
    return FigureTable(tuple(energies),tuple(wavelengths))


def _accessible_svg(path: Path) -> None:
    validate_asset(path)
    root=ET.parse(path).getroot()
    if root.tag!=SVG_NS+'svg' or root.attrib.get('role')!='img':
        raise OverviewFigureError('overview SVG lacks accessible image semantics')
    identifiers={}
    for node in root.iter():
        identifier=node.attrib.get('id')
        if identifier is not None:
            if not identifier or identifier in identifiers:raise OverviewFigureError('overview SVG identifiers are ambiguous')
            identifiers[identifier]=node
    labels=root.attrib.get('aria-labelledby','').split()
    if not labels or len(labels)!=len(set(labels)):
        raise OverviewFigureError('overview SVG accessible labels are missing or duplicated')
    for label in labels:
        labelled=identifiers.get(label)
        if labelled is None or labelled.tag not in {SVG_NS+'title',SVG_NS+'desc'} or not ''.join(labelled.itertext()).strip():
            raise OverviewFigureError('overview SVG accessible labels are unresolved or empty')


def validate_overview(contract: SourceContract) -> OverviewArtifacts:
    try:
        approved={item.path:item for item in contract.files if item.path in EXPECTED_PATHS}
        if set(approved)!=EXPECTED_PATHS:raise OverviewFigureError('approved overview figure set is absent or incomplete')
        if {item.validation_status for item in approved.values()}!={'calculated-unvalidated'}:
            raise OverviewFigureError('overview validation status is inconsistent')
        versions={item.version for item in approved.values()}
        if len(versions)!=1:raise OverviewFigureError('overview artifact versions are inconsistent')
        descriptor=_descriptor(contract.root/JSON_PATH,next(iter(versions)))
        table=_table(contract.root/CSV_PATH,descriptor.grid)
        _accessible_svg(contract.root/SVG_PATH)
        return OverviewArtifacts(descriptor,table)
    except OverviewFigureError:raise
    except (OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError,csv.Error,ET.ParseError) as exc:
        raise OverviewFigureError('invalid overview descriptor, table or SVG structure') from exc

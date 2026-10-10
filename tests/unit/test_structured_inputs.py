from pathlib import Path

import pytest

from tests.support.publication import create_repo, euvics_manifest, write_locks, pyeuvics_manifest
from tools.site_assembly.contracts import ContractError, _load_json, _strict_object, load_contract, load_locks
from tools.site_assembly.models import SourceLock


@pytest.mark.parametrize('raw', [
    b'{"a": 1, "a": 2}', b'{"nested": {"x": 1, "x": 2}}',
    b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}',
    b'{"x": "\xff"}', b'[]', b'null',
])
def test_invalid_json_is_a_labelled_contract_error(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / 'manifest.json'; path.write_bytes(raw)
    with pytest.raises(ContractError):
        _load_json(path)


@pytest.mark.parametrize('value', ['true', '1.0', 'null', '[]'])
def test_lock_version_requires_exact_integer(tmp_path: Path, value: str) -> None:
    path = write_locks(tmp_path / 'lock.yml', {'euvics': '1'*40, 'pyeuvics': '2'*40})
    path.write_text(path.read_text().replace('schema_version: 1', 'schema_version: '+value), encoding='utf-8')
    with pytest.raises(ContractError):
        load_locks(path)


@pytest.mark.parametrize('prefix', ['schema_version: 1\n', '1: value\n', 'null: value\n'])
def test_yaml_duplicate_or_nonstring_keys_fail(tmp_path: Path, prefix: str) -> None:
    path = write_locks(tmp_path / 'lock.yml', {'euvics': '1'*40, 'pyeuvics': '2'*40})
    path.write_text(prefix+path.read_text(), encoding='utf-8')
    with pytest.raises(ContractError):
        load_locks(path)


def test_mixed_mapping_keys_never_raise_sorting_typeerror() -> None:
    with pytest.raises(ContractError):
        _strict_object({1: 'bad', 'extra': 'bad'}, 'fixture', set())


@pytest.mark.parametrize('date', ['2026-02-30', '20261010', 20261010, True, ''])
def test_document_date_requires_real_iso_calendar_date(tmp_path: Path, date) -> None:
    manifest = euvics_manifest(); manifest['allowlist'] = manifest['allowlist'][:1]
    manifest['allowlist'][0]['document_date'] = date
    root = tmp_path / 'source'
    commit = create_repo(root, manifest, {'docs/overview.md': '# Fixture\n'})
    lock = SourceLock('euvics', 'https://github.com/pyeuvics/euvics', commit, 'publication/public-content-v1.json')
    with pytest.raises(ContractError, match='date'):
        load_contract(lock, root)


def test_candidate_status_container_fails_with_domain_error(tmp_path: Path) -> None:
    manifest = pyeuvics_manifest()
    manifest['candidate_sets'] = [{'status': [], 'name': 'bad', 'owner':'fixture', 'reason':'fixture', 'files':[], 'dependencies':[]}]
    root = tmp_path / 'source'
    commit = create_repo(root, manifest, {'CITATION.cff': 'cff-version: 1.2.0\n'})
    lock = SourceLock('pyeuvics', 'https://github.com/pyeuvics/pyEUVICS', commit, 'publication/public-content-v1.json')
    with pytest.raises(ContractError):
        load_contract(lock, root)

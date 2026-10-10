from pathlib import Path
import subprocess

import pytest

from tests.support.publication import create_sources, add_approved_notebook_set, add_proposal_release
from tools.site_assembly.contracts import ContractError, load_contract
from tools.site_assembly.models import SourceLock
from tools.site_assembly.pipeline import AssemblyError, _copy_contract


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def lock_for(name: str, commit: str) -> SourceLock:
    return SourceLock(name, f"https://github.com/pyeuvics/{'pyEUVICS' if name == 'pyeuvics' else 'euvics'}", commit, "publication/public-content-v1.json")


@pytest.mark.parametrize('role', ['ordinary', 'citation', 'dependency', 'pdf'])
def test_ignored_untracked_inputs_cannot_claim_locked_provenance(tmp_path: Path, role: str) -> None:
    euvics, pyeuvics, _ = create_sources(tmp_path)
    name, root, path = 'pyeuvics', pyeuvics, 'docs/index.md'
    if role == 'citation':
        path = 'CITATION.cff'
    elif role == 'dependency':
        add_approved_notebook_set(root, "print('fixture')\n")
        path = 'configs/fixture.yaml'
    elif role == 'pdf':
        name, root, path = 'euvics', euvics, 'build/proposal/main.pdf'
        add_proposal_release(root)
    git(root, 'rm', '--cached', '--', path)
    (root / '.gitignore').write_text(path + '\n', encoding='utf-8')
    git(root, 'add', '.gitignore')
    git(root, 'commit', '-qm', 'Exclude consumed synthetic file')
    assert git(root, 'status', '--porcelain') == ''
    with pytest.raises(ContractError, match='locked (Git )?tree|locked commit'):
        load_contract(lock_for(name, git(root, 'rev-parse', 'HEAD')), root)


def test_index_flags_cannot_hide_changed_consumed_bytes(tmp_path: Path) -> None:
    _, root, commits = create_sources(tmp_path)
    git(root, 'update-index', '--assume-unchanged', 'docs/index.md')
    (root / 'docs/index.md').write_text('# Changed\n', encoding='utf-8')
    assert git(root, 'status', '--porcelain') == ''
    with pytest.raises(ContractError, match='bytes differ'):
        load_contract(lock_for('pyeuvics', commits['pyeuvics']), root)


def test_copy_rechecks_bytes_after_contract_admission(tmp_path: Path) -> None:
    _, root, commits = create_sources(tmp_path)
    contract = load_contract(lock_for('pyeuvics', commits['pyeuvics']), root)
    git(root, 'update-index', '--assume-unchanged', 'docs/index.md')
    (root / 'docs/index.md').write_text('# Changed after admission\n', encoding='utf-8')
    with pytest.raises((ContractError, AssemblyError), match='bytes differ'):
        _copy_contract(contract, tmp_path / 'imported', '2026-10-10T00:00:00Z')

"""Versioned neutral expectations; no upstream code or private data is imported."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from tests.support.publication import create_sources, add_approved_notebook_set
from tools.site_assembly.contracts import ContractError, load_contract
from tools.site_assembly.models import SourceLock

CORPUS = json.loads((Path(__file__).parents[1] / 'fixtures/publication-contract-v1.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CORPUS['cases'], ids=lambda case: case['id'])
def test_neutral_producer_contract(case: dict, tmp_path: Path) -> None:
    assert CORPUS['corpus_version'] == '1.0'
    euvics, pyeuvics, _ = create_sources(tmp_path)
    root = euvics if case['source'] == 'euvics' else pyeuvics
    if case['fixture'] == 'notebook':
        add_approved_notebook_set(root, "print('neutral fixture')\n")
    path = root / 'publication/public-content-v1.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['schema_version'] = case['schema']
    if case['source'] == 'euvics' and case['schema'] == '1.1':
        for entry in manifest['allowlist']:
            entry['approval']['sha256'] = hashlib.sha256((root / entry['path']).read_bytes()).hexdigest()
    for change in case['edits']:
        target = manifest
        for key in change['path'][:-1]:
            target = target[int(key) if isinstance(target, list) else key]
        key = change['path'][-1]
        target[int(key) if isinstance(target, list) else key] = change['value']
    path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','commit','--allow-empty','-qm','Neutral contract variant'],cwd=root,check=True)
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    lock = SourceLock(case['source'], 'https://github.com/pyeuvics/'+('euvics' if case['source']=='euvics' else 'pyEUVICS'),commit,'publication/public-content-v1.json')
    if case['error']:
        with pytest.raises(ContractError,match=case['error']):
            load_contract(lock,root)
    else:
        contract = load_contract(lock,root)
        assert [entry.path for entry in contract.files] == case['files']
        assert [entry.path for entry in contract.notebooks] == case['notebooks']
        assert contract.lock == lock


@pytest.mark.parametrize('case', CORPUS['content_cases'], ids=lambda case: case['id'])
def test_neutral_content_policy(case: dict) -> None:
    from tools.site_assembly.models import PublishedFile
    from tools.site_assembly.pipeline import AssemblyError, _validate_rendered_links
    page = PublishedFile('pyeuvics', 'docs/index.md', 'markdown', 'Fixture', 'fixture',
                         'released', None, 'MIT', 'Synthetic fixture', ('No scientific claim.',))
    destinations = {'docs/guide.md': Path('imported/pyeuvics/docs/guide.md')}
    if case['error']:
        with pytest.raises(AssemblyError, match=case['error']):
            _validate_rendered_links(case['text'], page, destinations)
    else:
        _validate_rendered_links(case['text'], page, destinations)

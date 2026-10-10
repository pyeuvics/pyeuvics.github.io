"""Unexpected files cannot acquire ownership merely by reaching an output tree."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from tests.support.paths import ROOT
from tests.support.publication import create_sources, write_locks, init_repo
from tools.site_assembly import pipeline


def website_fixture(root: Path) -> Path:
    root.mkdir()
    for folder in ['content','overrides']:
        shutil.copytree(ROOT/folder,root/folder,symlinks=True)
    for relative in ['mkdocs.yml','requirements-docs.txt','requirements-notebooks.txt','docs/stylesheets/readthedocs.css']:
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,path)
    init_repo(root)
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','commit','-qm','Synthetic website'],cwd=root,check=True)
    return root


def inputs(tmp_path: Path, monkeypatch):
    sources=tmp_path/'sources';sources.mkdir()
    euvics,pyeuvics,commits=create_sources(sources)
    lock=write_locks(tmp_path/'sources.lock.yml',commits)
    monkeypatch.setenv('SOURCE_DATE_EPOCH','1785628800')
    return lock,euvics,pyeuvics


@pytest.mark.parametrize('extra',['extra.md','assets/extra.txt'])
def test_untracked_website_content_is_not_published(extra: str, tmp_path: Path, monkeypatch) -> None:
    website=website_fixture(tmp_path/'website')
    path=website/'content'/extra;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('unowned fixture',encoding='utf-8')
    lock,euvics,pyeuvics=inputs(tmp_path,monkeypatch)
    with pytest.raises(pipeline.AssemblyError,match='ownership'):
        pipeline.assemble_site(website,lock,euvics,pyeuvics,tmp_path/'output')
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('damage',['extra','missing','changed','symlink'])
def test_artifact_paths_and_copied_bytes_are_bound_to_expected_owners(damage: str, tmp_path: Path, monkeypatch) -> None:
    lock,euvics,pyeuvics=inputs(tmp_path,monkeypatch)
    original=pipeline._build_site
    def corrupt(*args):
        site=original(*args)
        if damage=='extra':(site/'unexpected.md').write_text('unowned',encoding='utf-8')
        elif damage=='missing':(site/'stylesheets/readthedocs.css').unlink()
        elif damage=='changed':
            with (site/'stylesheets/readthedocs.css').open('a',encoding='utf-8') as stream:stream.write('\n/* changed */\n')
        else:(site/'alias.txt').symlink_to('index.html')
        return site
    monkeypatch.setattr(pipeline,'_build_site',corrupt)
    with pytest.raises(pipeline.AssemblyError,match='ownership|checksum|symlink'):
        pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_complete_manifest_accounts_for_every_owned_artifact(tmp_path: Path, monkeypatch) -> None:
    lock,euvics,pyeuvics=inputs(tmp_path,monkeypatch)
    result=pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,tmp_path/'output')
    manifest=json.loads((result.output_root/'publication-artifact-manifest.json').read_text(encoding='utf-8'))
    actual={path.relative_to(result.site).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in result.site.rglob('*') if path.is_file()}
    assert {item['path']:item['sha256'] for item in manifest['files']}==actual
    records={item['path']:item for item in manifest['files']}
    assert records['search/search_index.json']['producer']=='material-search'
    assert records['stylesheets/readthedocs.css']['origin']=='website'
    assert records['imported/euvics/assets/diagram.svg']['owner']=='euvics'
    assert all(item['producer'] and item['input_sha256'] for item in records.values())
    assert any(item['origin']=='theme' and item['expected_sha256'] for item in records.values())
    assert len(result.inventory)==4  # Legacy source inventory remains compatible.


def test_extra_staged_page_fails_before_the_renderer_runs(tmp_path: Path, monkeypatch) -> None:
    lock,euvics,pyeuvics=inputs(tmp_path,monkeypatch)
    original=pipeline._materialize_build
    def inject(context):
        entries=original(context)
        (context.content/'injected.md').write_text('# Unowned',encoding='utf-8')
        return entries
    def forbidden(*args):pytest.fail('renderer ran before complete staged ownership validation')
    monkeypatch.setattr(pipeline,'_materialize_build',inject)
    monkeypatch.setattr(pipeline,'_build_site',forbidden)
    with pytest.raises(pipeline.AssemblyError,match='ownership'):
        pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,tmp_path/'output')


def test_only_canonical_internal_css_symlink_is_admitted(tmp_path: Path) -> None:
    from tools.site_assembly.website_inputs import website_inputs,WebsiteInputError
    website=website_fixture(tmp_path/'website')
    assert 'content/stylesheets/readthedocs.css' in website_inputs(website)
    (website/'content/alias.md').symlink_to('index.md')
    subprocess.run(['git','add','content/alias.md'],cwd=website,check=True)
    with pytest.raises(WebsiteInputError,match='symlink'):website_inputs(website)

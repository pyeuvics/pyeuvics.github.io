from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from tests.support.paths import ROOT
from tests.support.publication import create_sources, euvics_manifest, pyeuvics_manifest, write_locks, add_proposal_release, add_approved_notebook_set
from tools.site_assembly.contracts import load_contract, load_locks
from tools.site_assembly.staging import DestinationRegistry, PlannedOutput, OutputNamespace, OutputKind, StagingError, StagingPlan, create_staging_plan


def output(path: str) -> PlannedOutput:
    return PlannedOutput(path,'website','fixture',OutputKind.WEBSITE)


@pytest.mark.parametrize(('first','second'), [
    ('a.md','a.md'),('a','a/b.md'),('a/b.md','a'),('A.md','a.md'),
    ('Docs/a.md','docs/b.md'),('café.md','cafe\u0301.md'),
])
def test_duplicate_alias_and_file_directory_conflicts_are_rejected(first: str, second: str) -> None:
    registry=DestinationRegistry();registry.add(output(first))
    with pytest.raises(StagingError):registry.add(output(second))


@pytest.mark.parametrize('path',['','.', '../x','/x','a//b','a\\b','name.','name ','CON.md','aux/file','a:b','a?b'])
def test_output_names_must_be_portable_relative_paths(path: str) -> None:
    with pytest.raises(StagingError):DestinationRegistry().add(output(path))


def test_notebook_namespaces_cannot_be_claimed_by_another_producer() -> None:
    registry=DestinationRegistry();registry.reserve(OutputNamespace('notebook_assets','pyeuvics','notebook-assets',()))
    with pytest.raises(StagingError):registry.add(output('notebook_assets/image.png'))
    with pytest.raises(StagingError):registry.reserve(OutputNamespace('notebook_assets/subdir','website','other',()))


def test_dynamic_assets_require_the_planned_owner_and_portable_unique_paths() -> None:
    plan=StagingPlan((),(),(OutputNamespace('assets','pyeuvics','notebook-assets',()),),())
    assert plan.emitted_assets('pyeuvics',('assets/figure.png',))[0].owner=='pyeuvics'
    for owner,paths in [('website',('assets/figure.png',)),('pyeuvics',('outside.png',)),('pyeuvics',('assets/a.png','assets/A.png'))]:
        with pytest.raises(StagingError):plan.emitted_assets(owner,paths)


@pytest.mark.parametrize('mode',['zero','one','multiple','full'])
def test_staging_plan_is_deterministic_and_binds_exact_inputs(mode: str, tmp_path: Path) -> None:
    eu=euvics_manifest();py=pyeuvics_manifest()
    if mode=='zero':eu['allowlist']=[];py['allowlist']=[]
    if mode=='one':eu['allowlist']=eu['allowlist'][:1];py['allowlist']=[]
    euvics,pyeuvics,commits=create_sources(tmp_path,euvics=eu,pyeuvics=py)
    if mode=='full':
        commits['euvics']=add_proposal_release(euvics)
        commits['pyeuvics']=add_approved_notebook_set(pyeuvics,"print('planned')\n")
    locks=load_locks(write_locks(tmp_path/'sources.lock.yml',commits))
    contracts=tuple(load_contract(locks[name],root) for name,root in [('euvics',euvics),('pyeuvics',pyeuvics)])
    plan=create_staging_plan(ROOT,contracts)
    assert plan.to_dict()==create_staging_plan(ROOT,tuple(reversed(contracts))).to_dict()
    assert len({item.path for item in plan.outputs})==len(plan.outputs)
    assert all(item.owner and item.producer for item in plan.outputs)
    by_name={'euvics':euvics,'pyeuvics':pyeuvics,'website':ROOT}
    for item in plan.inputs:
        assert item.sha256==hashlib.sha256((by_name[item.source]/item.path).read_bytes()).hexdigest()
        if item.source!='website':assert item.commit==commits[item.source]
    assert str(tmp_path) not in json.dumps(plan.to_dict())
    if mode=='full':
        mapping=plan.source_destinations('euvics',Path('content'))
        assert mapping['build/proposal/main.pdf']==Path('content/documents/proposal.pdf')
        assert plan.output('documents/proposal.md').producer=='document-overview'
        assert plan.source_destinations('pyeuvics',Path('content'))['notebooks/00_environment_check.ipynb']==Path('content/software/notebooks/00_environment_check.md')


def test_planning_failure_occurs_before_output_or_document_work(tmp_path: Path, monkeypatch) -> None:
    from tools.site_assembly import pipeline
    euvics,pyeuvics,commits=create_sources(tmp_path)
    locks=write_locks(tmp_path/'sources.lock.yml',commits)
    def collision(*args):
        registry=DestinationRegistry();registry.add(output('same'));registry.add(output('same'))
    def forbidden(*args):
        pytest.fail('materialization began before a valid plan existed')
    monkeypatch.setattr(pipeline,'create_staging_plan',collision)
    monkeypatch.setattr(pipeline,'build_approved_documents',forbidden)
    monkeypatch.setenv('SOURCE_DATE_EPOCH','1785628800')
    with pytest.raises(pipeline.AssemblyError,match='duplicate destination'):
        pipeline.assemble_site(ROOT,locks,euvics,pyeuvics,tmp_path/'output')
    assert not (tmp_path/'output').exists()

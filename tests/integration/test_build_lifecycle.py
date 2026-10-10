import json
import os
from pathlib import Path

import pytest

from tests.support.paths import ROOT
from tests.support.publication import create_sources, write_locks
from tools.site_assembly import pipeline
from tools.validate_ci import _source_date_epoch


def test_failed_render_does_not_occupy_requested_output_and_retry_succeeds(tmp_path: Path, monkeypatch) -> None:
    euvics,pyeuvics,commits=create_sources(tmp_path)
    lock=write_locks(tmp_path/'sources.lock.yml',commits)
    monkeypatch.setenv('SOURCE_DATE_EPOCH','1785628800')
    original=pipeline._build_site
    def fail(*args):raise pipeline.AssemblyError('injected render failure')
    monkeypatch.setattr(pipeline,'_build_site',fail)
    destination=tmp_path/'output'
    with pytest.raises(pipeline.AssemblyError,match='injected render failure'):
        pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,destination)
    assert not destination.exists()
    incomplete=list(tmp_path.glob('.output.assembly-*/INCOMPLETE.json'))
    assert len(incomplete)==1
    assert json.loads(incomplete[0].read_text(encoding='utf-8'))['phase']=='render'
    monkeypatch.setattr(pipeline,'_build_site',original)
    result=pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,destination)
    assert result.output_root==destination
    assert (result.site/'index.html').is_file()
    assert not (destination/'INCOMPLETE.json').exists()
    assert incomplete[0].exists()


def test_ci_timestamp_derivation_does_not_mutate_process_environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv('SOURCE_DATE_EPOCH',raising=False)
    monkeypatch.setattr('tools.validate_ci.subprocess.check_output',lambda *args,**kwargs:'1785628800\n')
    assert _source_date_epoch(tmp_path)=='1785628800'
    assert 'SOURCE_DATE_EPOCH' not in os.environ


@pytest.mark.parametrize('value',['-1','+1','1.5','not-an-integer','9'*100])
def test_direct_and_ci_timestamp_validation_agree(value: str, tmp_path: Path, monkeypatch) -> None:
    from tools.validate_ci import ValidationError
    monkeypatch.setenv('SOURCE_DATE_EPOCH',value)
    with pytest.raises(pipeline.AssemblyError,match='SOURCE_DATE_EPOCH'):pipeline._build_timestamp()
    with pytest.raises(ValidationError,match='SOURCE_DATE_EPOCH'):_source_date_epoch(tmp_path)


def test_exclusive_promotion_never_replaces_an_existing_directory_even_after_precheck(tmp_path: Path, monkeypatch) -> None:
    from tools.site_assembly.promotion import promote_directory
    from tools.site_assembly.primitives import FileOperationError
    source=tmp_path/'owned';source.mkdir();(source/'result').write_text('verified',encoding='utf-8')
    target=tmp_path/'existing';target.mkdir();identity=target.stat().st_ino
    original=Path.exists
    monkeypatch.setattr(Path,'exists',lambda path: False if path==target else original(path))
    with pytest.raises(FileOperationError):promote_directory(source,target)
    assert target.stat().st_ino==identity
    assert not tuple(target.iterdir())
    assert (source/'result').read_text(encoding='utf-8')=='verified'


@pytest.mark.parametrize('phase',['materialize','render','verify','finalize'])
def test_each_phase_failure_retains_labelled_owned_workspace(tmp_path: Path, monkeypatch, phase: str) -> None:
    from tools.site_assembly.context import BuildInputs
    from tools.site_assembly.staging import StagingPlan
    from tools.site_assembly.timestamps import parse_timestamp
    from tools.site_assembly.rendering import load_renderer
    target=tmp_path/'output'
    inputs=BuildInputs(ROOT,target,parse_timestamp('1785628800'),(),StagingPlan((),(),(),()),load_renderer())
    monkeypatch.setattr(pipeline,'_prepare_build',lambda *args:inputs)
    def materialize(context):context.content.mkdir();return ()
    def render(context, entries):
        site=context.workspace/'site';site.mkdir();(site/'index.html').write_text('fixture',encoding='utf-8');return site
    monkeypatch.setattr(pipeline,'_materialize_build',materialize)
    monkeypatch.setattr(pipeline,'_render_build',render)
    monkeypatch.setattr(pipeline,'_verify_build',lambda *args:None)
    method=f'_{phase}_build';original=getattr(pipeline,method)
    def fail(*args):raise RuntimeError('synthetic phase failure')
    monkeypatch.setattr(pipeline,method,fail)
    with pytest.raises(pipeline.AssemblyError,match='synthetic phase failure'):
        pipeline.assemble_site(ROOT,Path('lock'),Path('euvics'),Path('pyeuvics'),target)
    assert not target.exists()
    marker=next(tmp_path.glob('.output.assembly-*/INCOMPLETE.json'))
    assert json.loads(marker.read_text(encoding='utf-8'))=={'status':'incomplete','phase':phase,'error_type':'RuntimeError'}
    monkeypatch.setattr(pipeline,method,original)
    result=pipeline.assemble_site(ROOT,Path('lock'),Path('euvics'),Path('pyeuvics'),target)
    assert result.site.is_dir()
    assert marker.exists()


def test_ci_review_manifest_failure_is_retryable_without_environment_mutation(tmp_path: Path, monkeypatch) -> None:
    from tools import validate_ci
    euvics,pyeuvics,commits=create_sources(tmp_path)
    lock=write_locks(tmp_path/'sources.lock.yml',commits)
    monkeypatch.delenv('SOURCE_DATE_EPOCH',raising=False)
    commands=[]
    monkeypatch.setattr(validate_ci,'_run',lambda *args:commands.append(args))
    def fake_assembly(website,lock,euvics,pyeuvics,output,*,source_date_epoch):
        assert source_date_epoch.isdigit()
        (output/'site').mkdir(parents=True)
        (output/'site/index.html').write_text('fixture',encoding='utf-8')
        (output/'staged-content-inventory.json').write_text('{"files":[]}',encoding='utf-8')
        for name in ('artifact-plan.json','publication-artifact-manifest.json','staging-plan.json'):
            (output/name).write_text('{}',encoding='utf-8')
    monkeypatch.setattr(validate_ci,'assemble_site',fake_assembly)
    from tools.validation_evidence import WebsiteIdentity,EnvironmentIdentity,ARTIFACT_EVIDENCE
    monkeypatch.setattr(validate_ci,'website_identity',lambda root:WebsiteIdentity('a'*40,'b'*64))
    monkeypatch.setattr(validate_ci,'environment_identity',lambda root:EnvironmentIdentity('3.13','c'*64,'fixture',(('requirements-docs.txt','d'*64),('requirements-notebooks.txt','e'*64)),(('fixture','1'),),'f'*64))
    original=validate_ci.write_review_manifest
    def fail(*args):raise validate_ci.ValidationError('injected manifest failure')
    monkeypatch.setattr(validate_ci,'write_review_manifest',fail)
    output=tmp_path/'review'
    with pytest.raises(validate_ci.ValidationError,match='injected manifest failure'):
        validate_ci.validate(ROOT,lock,euvics,pyeuvics,output)
    assert not output.exists()
    assert list(tmp_path.glob('.review.validation-*/INCOMPLETE.json'))
    monkeypatch.setattr(validate_ci,'write_review_manifest',original)
    result=validate_ci.validate(ROOT,lock,euvics,pyeuvics,output)
    assert result==output/'review-artifact-manifest.json'
    assert result.is_file()
    before_count=len(commands)
    reused=validate_ci.validate(ROOT,lock,euvics,pyeuvics,tmp_path/'reused',quality_receipt=output/'quality-record.json')
    assert reused.is_file()
    assert len(commands)-before_count==2  # Both source-contract validators still execute.
    assert 'SOURCE_DATE_EPOCH' not in os.environ
    assert all(command[2].isdigit() for command in commands)


def test_subprocess_timestamp_is_explicit_without_changing_parent(tmp_path: Path, monkeypatch) -> None:
    from tools import validate_ci
    from tools.site_assembly import documents
    monkeypatch.delenv('SOURCE_DATE_EPOCH',raising=False)
    seen=[]
    monkeypatch.setattr(validate_ci.subprocess,'run',lambda args,**kwargs:seen.append(kwargs['env']['SOURCE_DATE_EPOCH']))
    validate_ci._run(['fixture'],tmp_path,'1785628800')
    monkeypatch.setattr('tools.site_assembly.document_build.run_text',lambda *args,**kwargs:seen.append(kwargs['environment']['SOURCE_DATE_EPOCH']) or '')
    documents._run_make(tmp_path,'check','1785628800')
    assert seen==['1785628800','1785628800']
    assert 'SOURCE_DATE_EPOCH' not in os.environ

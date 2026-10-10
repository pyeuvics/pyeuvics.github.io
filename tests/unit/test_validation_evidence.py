from dataclasses import replace
import json
from pathlib import Path
import subprocess
import pytest
from tools.validation_evidence import (ARTIFACT_EVIDENCE,BUNDLE_FILES,EnvironmentIdentity,EvidenceError,environment_identity,lock_identity,read_record,requirement_identity,validate_pair,verify_bundle,website_identity,write_ancestry,write_bundle,write_record)
from tools.validate_ci import write_review_manifest
from tools.source_update import write_comparison
from tests.support.publication import init_repo,write_locks


@pytest.fixture
def evidence(tmp_path: Path):
    website=tmp_path/'website';website.mkdir();init_repo(website)
    (website/'README.md').write_text('fixture',encoding='utf-8')
    (website/'requirements-docs.txt').write_text('pytest==9.1.1\n',encoding='utf-8')
    (website/'requirements-notebooks.txt').write_text('numpy==2.5.1\n',encoding='utf-8')
    current=write_locks(website/'sources.lock.yml',{'euvics':'1'*40,'pyeuvics':'2'*40})
    subprocess.run(['git','add','.'],cwd=website,check=True);subprocess.run(['git','commit','-qm','Synthetic website'],cwd=website,check=True)
    root=tmp_path/'evidence';(root/'proposal').mkdir(parents=True)
    candidate=write_locks(root/'proposal/sources.lock.yml',{'euvics':'3'*40,'pyeuvics':'2'*40})
    identity=website_identity(website)
    env=EnvironmentIdentity('3.13','a'*64,'fixture',requirement_identity(website),(('fixture','1'),),'b'*64)
    for name,lock in [('baseline',current),('candidate',candidate)]:
        folder=root/name;(folder/'site').mkdir(parents=True)
        (folder/'site/index.html').write_text('synthetic '+name,encoding='utf-8')
        for file in ARTIFACT_EVIDENCE:(folder/file).write_text('{}',encoding='utf-8')
        write_review_manifest(folder);write_record(folder/'validation-record.json',identity,env,lock_identity(lock),'1785628800')
    write_ancestry(root/'ancestry.json',current,candidate)
    (root/'proposal/pull-request.md').write_text('fixture report',encoding='utf-8')
    (root/'proposal/pull-request.md.json').write_text('{}',encoding='utf-8')
    write_bundle(root,website,current,candidate)
    return root,website,current,candidate


def test_complete_evidence_round_trip_and_bound_report(evidence):
    root,website,current,candidate=evidence
    verify_bundle(root,website,current,candidate)
    report=root/'proposal/pull-request.md'
    write_comparison(current,candidate,root/'baseline/review-artifact-manifest.json',root/'candidate/review-artifact-manifest.json',report,root,website)
    assert 'Bound records confirm' in report.read_text(encoding='utf-8')
    assert 'not scientific approval' in report.read_text(encoding='utf-8')
    verify_bundle(root,website,current,candidate)


@pytest.mark.parametrize('name',BUNDLE_FILES)
def test_changed_evidence_file_is_rejected(name,evidence):
    root,website,current,candidate=evidence
    path=root/name;path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(EvidenceError,match='changed or mixed'):verify_bundle(root,website,current,candidate)


@pytest.mark.parametrize('damage',['missing-check','bool-version','unsupported-version','digest-number','epoch-bool','unknown-field','website-field','environment-field','ownership-missing','duplicate-package'])
def test_malformed_or_incomplete_records_fail(damage,evidence):
    root,_,_,_=evidence;path=root/'candidate/validation-record.json';raw=json.loads(path.read_text(encoding='utf-8'))
    if damage=='missing-check':raw['checks'].pop()
    elif damage=='bool-version':raw['validation_version']=True
    elif damage=='unsupported-version':raw['validation_version']=2
    elif damage=='digest-number':raw['artifact_manifest_sha256']=123
    elif damage=='epoch-bool':raw['epoch']=True
    elif damage=='unknown-field':raw['unknown']=1
    elif damage=='website-field':del raw['website']['inputs_sha256']
    elif damage=='environment-field':del raw['environment']['installed_files_sha256']
    elif damage=='ownership-missing':raw['evidence']=[]
    else:raw['environment']['packages']*=2
    path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(EvidenceError):read_record(path)


@pytest.mark.parametrize('damage',['environment','epoch','website','lock','ownership','manifest','ancestry'])
def test_mixed_validation_inputs_fail_before_envelope_creation(damage,evidence):
    root,website,current,candidate=evidence;path=root/'candidate/validation-record.json';raw=json.loads(path.read_text(encoding='utf-8'))
    if damage=='environment':raw['environment']['installed_files_sha256']='c'*64
    elif damage=='epoch':raw['epoch']='1'
    elif damage=='website':raw['website']['commit']='d'*40
    elif damage=='lock':raw['lock']['euvics']='e'*40
    elif damage=='ownership':raw['evidence'][0][1]='f'*64
    elif damage=='manifest':raw['artifact_manifest_sha256']='0'*64
    else:(root/'ancestry.json').write_text('{}',encoding='utf-8')
    path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(EvidenceError):validate_pair(root,website,current,candidate)


def test_assume_unchanged_does_not_hide_website_changes(evidence):
    _,website,_,_=evidence
    subprocess.run(['git','update-index','--assume-unchanged','README.md'],cwd=website,check=True)
    (website/'README.md').write_text('changed',encoding='utf-8')
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=website)
    with pytest.raises(EvidenceError,match='bytes differ'):website_identity(website)


def test_stale_website_revision_is_rejected(evidence):
    root,website,current,candidate=evidence
    (website/'README.md').write_text('new revision',encoding='utf-8')
    subprocess.run(['git','commit','-qam','New synthetic revision'],cwd=website,check=True)
    with pytest.raises(EvidenceError,match='stale'):verify_bundle(root,website,current,candidate)


def test_missing_evidence_never_produces_a_passed_validation_claim(evidence):
    root,_,current,candidate=evidence;report=root/'comparison-only.md'
    write_comparison(current,candidate,root/'baseline/review-artifact-manifest.json',root/'candidate/review-artifact-manifest.json',report)
    text=report.read_text(encoding='utf-8')
    assert 'Comparison only' in text and 'Both complete artifacts passed' not in text and 'Bound records confirm' not in text


def test_installed_file_changes_alter_environment_fingerprint(tmp_path: Path,monkeypatch):
    from tools import validation_evidence as module
    environment=tmp_path/'env';environment.mkdir();library=environment/'module.py';library.write_text('one',encoding='utf-8')
    for name in module.REQUIREMENTS:(tmp_path/name).write_text('fixture==1',encoding='utf-8')
    class Distribution:
        metadata={'Name':'fixture'};version='1';files=(Path('module.py'),)
        def locate_file(self,path):return environment/path
    monkeypatch.setattr(module,'distributions',lambda:[Distribution()]);monkeypatch.setattr(module.sys,'prefix',str(environment))
    first=environment_identity(tmp_path);library.write_text('two',encoding='utf-8')
    assert first.installed_files_sha256!=environment_identity(tmp_path).installed_files_sha256

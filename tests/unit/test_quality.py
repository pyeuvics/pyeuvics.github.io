import json
from pathlib import Path
import subprocess
import pytest
from tools.quality import QualityError,run_checks,source_only,verify_receipt,write_receipt
from tools.validation_evidence import WebsiteIdentity,EnvironmentIdentity

WEBSITE=WebsiteIdentity('a'*40,'b'*64)
ENVIRONMENT=EnvironmentIdentity('3.13','c'*64,'fixture',(('requirements-docs.txt','d'*64),('requirements-notebooks.txt','e'*64)),(('fixture','1'),),'f'*64)


def test_source_only_needs_no_source_repositories_and_does_not_mint_reusable_dirty_evidence(tmp_path: Path):
    root=tmp_path/'website';root.mkdir();calls=[]
    record=source_only(root,tmp_path/'output','1785628800',runner=lambda *args:calls.append(args))
    assert len(calls)==4
    assert [call[0][2] for call in calls]==['tools.dependencies','pytest','mypy','mkdocs']
    assert all(call[1]==root and call[2]=='1785628800' for call in calls)
    assert 'tools' in calls[2][0] and 'tests/support' in calls[2][0] and '--strict' in calls[2][0]
    assert json.loads(record.read_text(encoding='utf-8'))['website'] is None
    with pytest.raises(QualityError):verify_receipt(record,WEBSITE,ENVIRONMENT,'1785628800')


@pytest.mark.parametrize('change',['version','policy','website','environment','epoch','checks','extra'])
def test_quality_reuse_rejects_changed_or_incomplete_inputs(change,tmp_path: Path):
    path=tmp_path/'quality.json';write_receipt(path,WEBSITE,ENVIRONMENT,'1785628800')
    verify_receipt(path,WEBSITE,ENVIRONMENT,'1785628800')
    raw=json.loads(path.read_text(encoding='utf-8'))
    if change=='version':raw['quality_version']=True
    elif change=='policy':raw['policy']='older-policy'
    elif change=='website':raw['website']['inputs_sha256']='0'*64
    elif change=='environment':raw['environment']['installed_files_sha256']='0'*64
    elif change=='epoch':raw['epoch']='1'
    elif change=='checks':raw['checks'].pop()
    else:raw['extra']='unreviewed'
    path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(QualityError):verify_receipt(path,WEBSITE,ENVIRONMENT,'1785628800')


def test_new_untyped_tool_fails_the_shared_quality_stage(tmp_path: Path):
    (tmp_path/'tools').mkdir();(tmp_path/'tests/support').mkdir(parents=True)
    (tmp_path/'tools/new_tool.py').write_text('def untyped(value):\n    return value\n',encoding='utf-8')
    (tmp_path/'tests/support/helper.py').write_text('VALUE: int = 1\n',encoding='utf-8')
    seen=[]
    def runner(args,root,epoch):
        seen.append(args[2])
        if args[2]=='mypy':
            result=subprocess.run(args,cwd=root,text=True,capture_output=True)
            assert 'new_tool.py' in result.stdout and 'missing a type annotation' in result.stdout
            if result.returncode:raise QualityError('typing failed')
    with pytest.raises(QualityError):run_checks(tmp_path,tmp_path/'checks','1785628800',runner)
    assert seen==['tools.dependencies','pytest','mypy']


@pytest.mark.parametrize('changed',[False,True])
def test_bound_source_quality_checks_inputs_again_before_promotion(changed,tmp_path: Path,monkeypatch):
    from tools import quality
    identities=iter([WEBSITE,WebsiteIdentity('a'*40,'0'*64) if changed else WEBSITE])
    monkeypatch.setattr(quality,'website_identity',lambda root:next(identities))
    monkeypatch.setattr(quality,'environment_identity',lambda root:ENVIRONMENT)
    output=tmp_path/'output'
    if changed:
        with pytest.raises(QualityError):source_only(tmp_path,output,'1785628800',True,lambda *args:None)
        assert not output.exists()
        assert list(tmp_path.glob('.output.quality-*/INCOMPLETE.json'))
    else:
        receipt=source_only(tmp_path,output,'1785628800',True,lambda *args:None)
        verify_receipt(receipt,WEBSITE,ENVIRONMENT,'1785628800')

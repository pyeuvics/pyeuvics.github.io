import json
from pathlib import Path
import pytest
from tools.review_manifest import ReviewManifestError,parse_review_manifest,read_review_manifest,write_manifest,ReviewFile,ReviewManifest,compare_artifacts
from tools.source_update import SourceUpdateError,_read_review_manifest,write_comparison
from tools.validate_ci import write_review_manifest,ValidationError
from tests.support.publication import write_locks


def valid():return {'manifest_version':1,'files':[{'path':'site/a.html','sha256':'a'*64,'bytes':10}]}


@pytest.mark.parametrize('damage',['null-root','list-root','scalar-root','bool-version','new-version','extra-root','not-list','scalar-entry','extra-entry','number-digest','null-digest','short-digest','bool-bytes','float-bytes','negative-bytes','absolute-path','traversal','backslash','control','bidi','non-nfc','duplicate','case-alias','order'])
def test_malformed_review_records_raise_domain_errors(damage,tmp_path: Path):
    raw=valid();item=raw['files'][0]
    if damage=='null-root':raw=None
    elif damage=='list-root':raw=[]
    elif damage=='scalar-root':raw=7
    elif damage=='bool-version':raw['manifest_version']=True
    elif damage=='new-version':raw['manifest_version']=2
    elif damage=='extra-root':raw['unexpected']=1
    elif damage=='not-list':raw['files']={}
    elif damage=='scalar-entry':raw['files']=[False]
    elif damage=='extra-entry':item['unexpected']=1
    elif damage=='number-digest':item['sha256']=7
    elif damage=='null-digest':item['sha256']=None
    elif damage=='short-digest':item['sha256']='aa'
    elif damage=='bool-bytes':item['bytes']=True
    elif damage=='float-bytes':item['bytes']=1.0
    elif damage=='negative-bytes':item['bytes']=-1
    elif damage=='absolute-path':item['path']='/site/a'
    elif damage=='traversal':item['path']='site/../a'
    elif damage=='backslash':item['path']='site\\a'
    elif damage=='control':item['path']='site/a\n'
    elif damage=='bidi':item['path']='site/a\u202ehtml'
    elif damage=='non-nfc':item['path']='site/cafe\u0301.html'
    elif damage=='duplicate':raw['files'].append(dict(item))
    elif damage=='case-alias':raw['files'].append(dict(item,path='site/A.html'))
    else:raw['files']=[dict(item,path='site/z.html'),item]
    with pytest.raises(ReviewManifestError):parse_review_manifest(raw)
    path=tmp_path/'manifest.json';path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(SourceUpdateError):_read_review_manifest(path)


def test_existing_version_one_manifest_round_trips(tmp_path: Path):
    model=parse_review_manifest(valid());path=tmp_path/'review.json';write_manifest(path,model)
    assert read_review_manifest(path)==model
    assert model.files==(ReviewFile('site/a.html','a'*64,10),)


def test_complete_comparison_includes_byte_metadata_changes():
    before=ReviewManifest((ReviewFile('site/a','a'*64,1),ReviewFile('site/old','b'*64,2)))
    after=ReviewManifest((ReviewFile('site/a','a'*64,2),ReviewFile('site/new','c'*64,3)))
    result=compare_artifacts(before,after)
    assert result.added==('site/new',) and result.removed==('site/old',) and result.changed==('site/a',)


def test_report_discloses_truncation_and_retains_complete_json(tmp_path: Path):
    current=write_locks(tmp_path/'current.yml',{'euvics':'1'*40,'pyeuvics':'2'*40})
    candidate=write_locks(tmp_path/'candidate.yml',{'euvics':'3'*40,'pyeuvics':'2'*40})
    baseline=tmp_path/'baseline.json';proposed=tmp_path/'candidate.json'
    write_manifest(baseline,ReviewManifest(()))
    write_manifest(proposed,ReviewManifest(tuple(ReviewFile(f'site/{i:03d}.html','a'*64,1) for i in range(103))))
    report=tmp_path/'report.md';write_comparison(current,candidate,baseline,proposed,report)
    assert 'Showing 100 of 103 paths; 3 omitted' in report.read_text(encoding='utf-8')
    complete=json.loads((tmp_path/'report.md.json').read_text(encoding='utf-8'))
    assert len(complete['added'])==103 and complete['added'][-1]=='site/102.html'


def test_review_writer_rejects_aliased_files(tmp_path: Path):
    site=tmp_path/'site';site.mkdir();(tmp_path/'staged-content-inventory.json').write_text('{}',encoding='utf-8')
    target=tmp_path/'secret.txt';target.write_text('private',encoding='utf-8');(site/'alias.txt').symlink_to(target)
    with pytest.raises(ValidationError,match='aliased'):write_review_manifest(tmp_path)


def test_duplicate_json_keys_are_rejected(tmp_path: Path):
    path=tmp_path/'review.json';path.write_text('{"manifest_version":1,"manifest_version":1,"files":[]}',encoding='utf-8')
    with pytest.raises(ReviewManifestError):read_review_manifest(path)

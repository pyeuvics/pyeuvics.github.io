from dataclasses import replace
from pathlib import Path
import shutil
import json
import subprocess
import pytest
from tests.support.paths import ROOT
from tests.support.publication import create_sources,euvics_manifest,pyeuvics_manifest,write_locks,add_proposal_release,add_approved_notebook_set,add_approved_campaign_set
from tools.site_assembly.contracts import load_contract,load_locks
from tools.site_assembly.staging import create_staging_plan
from tools.site_assembly.publication_pages import stage_publication_indexes
from tools.site_assembly.entry_pages import stage_source_entry_pages
from tools.site_assembly.campaign_pages import stage_campaign_overviews
from tools.site_assembly.template_slots import fill_slot,TemplateSlotError
from tools.site_assembly.models import InventoryEntry
from tools.site_assembly.primitives import sha256_file


@pytest.mark.parametrize('mode',['none','partial','full'])
def test_publication_view_drives_consistent_indexes(mode: str,tmp_path: Path) -> None:
    eu=euvics_manifest();py=pyeuvics_manifest()
    if mode=='none':eu['allowlist']=[];py['allowlist']=[]
    e,p,commits=create_sources(tmp_path,euvics=eu,pyeuvics=py)
    if mode=='full':
        commits['euvics']=add_proposal_release(e)
        commits['pyeuvics']=add_approved_notebook_set(p,"print('approved')\n")
        previous=json.loads((p/'publication/public-content-v1.json').read_text(encoding='utf-8'))['candidate_sets']
        add_approved_campaign_set(p)
        manifest_path=p/'publication/public-content-v1.json'
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'));manifest['candidate_sets'].extend(previous)
        manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        subprocess.run(['git','add','.'],cwd=p,check=True)
        subprocess.run(['git','commit','-qm','Combine synthetic approvals'],cwd=p,check=True)
        commits['pyeuvics']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()
    locks=load_locks(write_locks(tmp_path/'sources.lock.yml',commits))
    contracts=tuple(load_contract(locks[name],path) for name,path in [('euvics',e),('pyeuvics',p)])
    plan=create_staging_plan(ROOT,contracts);root=tmp_path/'staged';shutil.copytree(ROOT/'content',root)
    receipts=[]
    for source in plan.publication:
        for item in source.downloads:
            target=source.destination(item.path);path=root/target;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(e/item.path,path);digest=sha256_file(path)
            receipts.append(InventoryEntry(source.lock.name,item.path,target,digest,digest,item.publication_status,item.known_limitations))
    inventory=tuple(receipts)
    for _ in range(2):
        stage_source_entry_pages(plan.publication,root,root/'imported','2026-10-10T00:00:00Z')
        stage_campaign_overviews(next(item for item in plan.publication if item.lock.name=='pyeuvics'),root,'2026-10-10T00:00:00Z')
        stage_publication_indexes(plan.publication,inventory,root,'2026-10-10T00:00:00Z')
        current={str(path.relative_to(root)):path.read_bytes() for path in root.rglob('*.md')}
        if _==0:before=current
        else:assert before==current
    home=(root/'index.md').read_text(encoding='utf-8')
    assert home.count('## Approved content in this assembled build')==1
    assert str(len(next(item for item in plan.publication if item.lock.name=='pyeuvics').files))+' manifest-approved pyEUVICS files' in home
    downloads=(root/'downloads/index.md').read_text(encoding='utf-8')
    assert 'scaffold' not in downloads
    assert 'Approved items: '+('1' if mode=='full' else '0') in downloads
    assert '.csv)' not in downloads and '.ipynb)' not in downloads
    if mode=='full':
        assert inventory[0].staged_sha256 in downloads
        for value in ['SHA-256','Bytes','License','Attribution','Document date','Known limitations']:assert value in downloads
        assert 'Approved items: 1' in (root/'software/notebooks/index.md').read_text(encoding='utf-8')
        assert 'Approved items: 1' in (root/'campaigns/index.md').read_text(encoding='utf-8')
        with pytest.raises(ValueError,match='receipt'):stage_publication_indexes(plan.publication,(),root,'time')
        bad=(replace(inventory[0],staged_sha256='0'*64),)
        with pytest.raises(ValueError,match='receipt'):stage_publication_indexes(plan.publication,bad,root,'time')


@pytest.mark.parametrize('text',['none','<!-- publication:x:start -->','<!-- publication:x:end --><!-- publication:x:start -->','<!-- publication:x:start --><!-- publication:x:start --><!-- publication:x:end -->'])
def test_template_slots_fail_closed(text: str,tmp_path: Path) -> None:
    path=tmp_path/'page.md';path.write_text(text,encoding='utf-8')
    with pytest.raises(TemplateSlotError):fill_slot(path,'x','body')
    assert path.read_text(encoding='utf-8')==text


def test_template_slot_replacement_preserves_prose_and_is_idempotent(tmp_path: Path) -> None:
    path=tmp_path/'page.md';path.write_text('before\n<!-- publication:x:start -->old<!-- publication:x:end -->\nafter',encoding='utf-8')
    fill_slot(path,'x','new');first=path.read_bytes();fill_slot(path,'x','new')
    assert path.read_bytes()==first
    assert path.read_text(encoding='utf-8')=='before\n<!-- publication:x:start -->\nnew\n<!-- publication:x:end -->\nafter'

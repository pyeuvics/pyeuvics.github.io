"""Document release matrix exercises real disposable Make builds and PDFs."""
import json
from pathlib import Path
import subprocess

import pytest

from tests.support.publication import create_sources, add_proposal_release, write_locks, snapshot
from tools.ci_source_locks import inspect_euvics
from tools.site_assembly.contracts import load_contract,load_locks
from tools.site_assembly.document_policy import document_requirements,DocumentError
from tools.site_assembly.document_build import build_documents,inspect_logs


def candidate(tmp_path: Path, roles: tuple[str,...]):
    euvics,_,commits=create_sources(tmp_path)
    if roles:
        add_proposal_release(euvics)
        path=euvics/'publication/public-content-v1.json';manifest=json.loads(path.read_text(encoding='utf-8'))
        template=manifest['allowlist'].pop()
        for role in roles:
            entry=dict(template,path=f'build/{role}/main.pdf',title=f'Generic {role}')
            manifest['allowlist'].append(entry)
            destination=euvics/entry['path'];destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((euvics/'document_sources/proposal.pdf').read_bytes())
        if 'proposal' not in roles:(euvics/'build/proposal/main.pdf').unlink()
        path.write_text(json.dumps(manifest),encoding='utf-8')
        recipes=''.join(f'\t@mkdir -p build/{role}\n\t@cp document_sources/proposal.pdf build/{role}/main.pdf\n\t@printf public > build/{role}/main.log\n' for role in roles)
        (euvics/'Makefile').write_text('.PHONY: verify-archive check\nverify-archive:\n\t@true\ncheck:\n'+recipes,encoding='utf-8')
        subprocess.run(['git','add','-f','.'],cwd=euvics,check=True)
        subprocess.run(['git','commit','-qm','Synthetic release matrix'],cwd=euvics,check=True)
        commits['euvics']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=euvics,text=True).strip()
    lock=write_locks(tmp_path/'sources.lock.yml',commits)
    return euvics,lock,load_contract(load_locks(lock)['euvics'],euvics)


@pytest.mark.parametrize('roles',[(),('proposal',),('cdr',),('proposal','cdr')])
def test_document_requirements_build_and_evidence_matrix(tmp_path: Path,roles: tuple[str,...]) -> None:
    source,lock,contract=candidate(tmp_path,roles);before=snapshot(source)
    requirements=document_requirements(contract)
    assert requirements.roles==tuple(sorted(roles))
    assert inspect_euvics(lock,source)==(f"pdf_candidate={'true' if roles else 'false'}",)
    result=build_documents(contract,requirements,tmp_path/'output','1785628800')
    assert snapshot(source)==before
    assert {item.entry.path for item in result.documents}=={f'build/{role}/main.pdf' for role in roles}
    if roles:
        evidence=json.loads((tmp_path/'output/source-build/document-build-evidence.json').read_text(encoding='utf-8'))
        assert evidence['source_commit']==contract.lock.commit
        assert any(item['name']=='make' and item['status']=='available' for item in evidence['toolchain'])
        assert len(evidence['logs'])==len(roles)
        assert {item['sha256'] for item in evidence['documents']}=={item.sha256 for item in result.documents}
        for item in result.documents:assert item.rebuilt.read_bytes()==(source/item.entry.path).read_bytes()
    else:
        assert requirements.make_executable is None
        assert not (tmp_path/'output').exists()


def test_candidate_indicator_does_not_claim_release_approval(tmp_path: Path) -> None:
    source,lock,contract=candidate(tmp_path,('proposal',))
    from dataclasses import replace
    bad=replace(contract,files=tuple(replace(item,document_date='2026-02-30') if item.kind=='pdf' else item for item in contract.files))
    assert inspect_euvics(lock,source)==('pdf_candidate=true',)
    with pytest.raises(DocumentError,match='date'):document_requirements(bad)


@pytest.mark.parametrize('damage',['encoding','citation','symlink','size'])
def test_document_log_evidence_is_bounded_and_fail_closed(tmp_path: Path,damage: str) -> None:
    build=tmp_path/'build';build.mkdir();path=build/'main.log'
    if damage=='encoding':path.write_bytes(b'\xff')
    elif damage=='citation':path.write_text('There were undefined references',encoding='utf-8')
    elif damage=='size':path.write_bytes(b'x'*8_388_609)
    else:path.symlink_to('missing')
    with pytest.raises(DocumentError):inspect_logs(tmp_path)


def test_missing_document_toolchain_is_reported_before_build(tmp_path: Path,monkeypatch) -> None:
    _,_,contract=candidate(tmp_path,('proposal',))
    monkeypatch.setattr('tools.site_assembly.document_policy.shutil.which',lambda _:None)
    with pytest.raises(DocumentError,match='toolchain'):document_requirements(contract)


def test_document_toolchain_change_prevents_publication(tmp_path: Path,monkeypatch) -> None:
    from tools.site_assembly import document_build
    from tools.site_assembly.document_toolchain import ToolVersion
    _,_,contract=candidate(tmp_path,('proposal',))
    observations=iter([(ToolVersion('make','available','one','a'*64,'b'*64),),(ToolVersion('make','available','two','c'*64,'d'*64),)])
    monkeypatch.setattr(document_build,'capture_toolchain',lambda:next(observations))
    with pytest.raises(DocumentError,match='toolchain changed'):
        build_documents(contract,document_requirements(contract),tmp_path/'output','1785628800')

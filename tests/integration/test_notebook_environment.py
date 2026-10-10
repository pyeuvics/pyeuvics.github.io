"""A hostile global python3 kernel cannot replace the selected interpreter."""
import hashlib
import json
from pathlib import Path
import sys
from tests.support.paths import ROOT
from tests.support.publication import create_sources,add_approved_notebook_set,write_locks,snapshot
from tools.site_assembly import assemble_site


def test_real_owned_kernel_and_environment_provenance(tmp_path: Path,monkeypatch) -> None:
    fake=tmp_path/'hostile/kernels/python3';fake.mkdir(parents=True)
    (fake/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-c','raise RuntimeError("global kernel selected")'],'display_name':'Hostile global fixture','language':'python'}),encoding='utf-8')
    monkeypatch.setenv('JUPYTER_PATH',str(tmp_path/'hostile'))
    euvics,pyeuvics,commits=create_sources(tmp_path)
    code="import sys, hashlib\nfrom pathlib import Path\nprint('kernel-sha', hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest())\n"
    commits['pyeuvics']=add_approved_notebook_set(pyeuvics,code)
    before=snapshot(pyeuvics)
    locks=write_locks(tmp_path/'sources.lock.yml',commits)
    result=assemble_site(ROOT,locks,euvics,pyeuvics,tmp_path/'output',source_date_epoch='1785628800')
    assert snapshot(pyeuvics)==before
    provenance=json.loads((result.output_root/'notebook-execution-provenance.json').read_text(encoding='utf-8'))['notebooks'][0]
    expected=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
    assert provenance['environment']['interpreter_sha256']==expected
    assert provenance['matching_executions']==2
    assert provenance['source_commit']==commits['pyeuvics']
    page=(result.staged_content/'software/notebooks/00_environment_check.md').read_text(encoding='utf-8')
    assert 'kernel-sha '+expected in page
    assert provenance['environment_sha256'] in page
    assert 'Python hash seed' in page and 'no RNG seed is injected' in page
    assert not (result.output_root/'source-build/notebook-runtime-home/runtime/connection.json').exists()

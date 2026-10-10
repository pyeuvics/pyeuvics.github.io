from dataclasses import asdict
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import pytest
from tools.site_assembly import document_toolchain as module


def test_missing_optional_tools_are_explicit(monkeypatch):
    monkeypatch.setattr(module.shutil,'which',lambda name:None)
    result=module.capture_toolchain()
    assert {item.name for item in result}=={'make','latexmk','pdflatex','kpsewhich','fc-list','dpkg-query'}
    assert all(item.status=='unavailable' and item.version=='' for item in result)


@pytest.mark.parametrize('mode',['normal','private','timeout','large'])
def test_version_probes_are_bounded_and_withhold_private_text(mode,tmp_path: Path,monkeypatch):
    executable=tmp_path/'make';executable.write_text('fixture binary',encoding='utf-8')
    monkeypatch.setattr(module.shutil,'which',lambda name:str(executable) if name=='make' else None)
    def run(args,**kwargs):
        assert kwargs['timeout']==15 and args==[str(executable),'--version']
        if mode=='timeout':raise subprocess.TimeoutExpired(args,15)
        text='GNU Make 3.81\n' if mode=='normal' else '/Users/private-person/internal\n' if mode=='private' else 'x'*131073
        kwargs['stdout'].write(text.encode());return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module.subprocess,'run',run)
    record=module.capture_toolchain()[0]
    if mode in {'timeout','large'}:assert record.status=='probe-failed'
    else:
        assert record.status=='available' and len(record.executable_sha256)==len(record.report_sha256)==64
        if mode=='normal':assert record.version=='GNU Make 3.81'
        else:assert '/Users/' not in json.dumps(asdict(record)) and 'withheld' in record.version

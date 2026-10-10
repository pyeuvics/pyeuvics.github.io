"""Format rejection is enforced before an admitted source asset is copied."""
from pathlib import Path
import subprocess
import pytest
from tests.support.paths import ROOT
from tests.support.publication import create_sources, write_locks
from tools.site_assembly import pipeline


def test_admitted_svg_script_fails_before_site_builder(tmp_path: Path, monkeypatch) -> None:
    euvics,pyeuvics,commits=create_sources(tmp_path)
    (euvics/'assets/diagram.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',encoding='utf-8')
    subprocess.run(['git','add','assets/diagram.svg'],cwd=euvics,check=True)
    subprocess.run(['git','commit','-qm','Synthetic active asset'],cwd=euvics,check=True)
    commits['euvics']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=euvics,text=True).strip()
    lock=write_locks(tmp_path/'sources.lock.yml',commits)
    def forbidden(*args):pytest.fail('site builder ran with an unsafe source asset')
    monkeypatch.setattr(pipeline,'_build_site',forbidden)
    with pytest.raises(pipeline.AssemblyError,match='bounded format/privacy'):
        pipeline.assemble_site(ROOT,lock,euvics,pyeuvics,tmp_path/'output',source_date_epoch='1785628800')
    assert not (tmp_path/'output').exists()
    assert not list(tmp_path.glob('.output.assembly-*/content/imported/euvics/assets/diagram.svg'))

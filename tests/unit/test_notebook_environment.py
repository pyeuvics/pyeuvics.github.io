"""Explicit interpreter selection and frozen source environment checks."""
from dataclasses import replace
from pathlib import Path
import sys
import pytest
import yaml

from tests.support.publication import notebook_spec as spec
from tools.site_assembly import notebook_environment as environment
from tools.site_assembly.notebook_policy import NotebookError


def test_owned_kernel_ignores_global_python_registration(tmp_path: Path,monkeypatch) -> None:
    monkeypatch.setenv('JUPYTER_PATH',str(tmp_path/'hostile-global'))
    manager=environment.owned_kernel(tmp_path/'owned')
    assert manager.kernel_name=='publication'
    kernel=manager.kernel_spec_manager.get_kernel_spec('publication')
    assert kernel.argv==[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    assert manager.kernel_spec_manager.ensure_native_kernel is False
    assert manager.kernel_spec_manager.kernel_dirs==[str(tmp_path/'owned/kernels')]


@pytest.mark.parametrize('expected',['2.5.1','0.0-wrong'])
def test_declared_source_policy_controls_numerical_environment(tmp_path: Path,expected: str) -> None:
    path=tmp_path/'environment.yaml'
    path.write_text(yaml.safe_dump({'schema_version':1,'python':'>=3.13','versions':{'numpy':expected,'pyEUVICS':spec().package_version}}),encoding='utf-8')
    policy_spec=replace(spec(),configurations=('environment.yaml',))
    if expected=='2.5.1':
        result=environment.validate_source_environments(policy_spec,tmp_path,{'numpy':'2.5.1'})
        assert len(result)==1 and result[0][0]=='environment.yaml'
    else:
        with pytest.raises(NotebookError,match='mismatch for numpy'):
            environment.validate_source_environments(policy_spec,tmp_path,{'numpy':'2.5.1'})


def test_website_dependency_mismatch_is_explicit(tmp_path: Path,monkeypatch) -> None:
    monkeypatch.setattr(environment,'version',lambda name:'0.0-wrong')
    with pytest.raises(NotebookError,match='website execution environment mismatch'):
        environment.capture_environment(spec(),tmp_path,{})


def test_invalid_hash_seed_fails_before_kernel_start(tmp_path: Path) -> None:
    with pytest.raises(NotebookError,match='unsigned 32-bit'):
        environment.capture_environment(replace(spec(),random_seed=str(2**32)),tmp_path,{})


def test_environment_fingerprint_binds_source_inputs_without_local_paths(tmp_path: Path) -> None:
    first=environment.capture_environment(spec(),tmp_path,{'fixture.ipynb':'a'*64})
    second=environment.capture_environment(spec(),tmp_path,{'fixture.ipynb':'b'*64})
    assert first.fingerprint!=second.fingerprint
    assert first.interpreter_sha256==second.interpreter_sha256
    assert first.packages and all(len(record)==64 for _,_,record in first.packages)
    import json
    assert str(tmp_path) not in json.dumps(first.to_dict())
    assert str(Path(sys.executable).parent) not in json.dumps(first.to_dict())


def test_upgraded_website_versions_do_not_override_frozen_source_policy(tmp_path: Path) -> None:
    path=tmp_path/'environment.yaml'
    path.write_text(yaml.safe_dump({'schema_version':1,'python':'>=3.13',
        'versions':{'numpy':'2.5.1','scipy':'1.18.0'}}),encoding='utf-8')
    policy_spec=replace(spec(),configurations=('environment.yaml',))
    with pytest.raises(NotebookError,match='locked source environment mismatch for numpy'):
        environment.validate_source_environments(policy_spec,tmp_path,{'numpy':'2.5.3','scipy':'1.18.1'})

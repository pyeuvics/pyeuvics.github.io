import json
from importlib.metadata import PackageNotFoundError
from pathlib import Path
import shutil
import pytest
from tools.dependencies import DependencyError,check_policy,checked_versions,read_pins
from tests.support.paths import ROOT


@pytest.mark.parametrize('text',['example','example>=1','example==1.*','example[extra]==1','example==1; python_version>"3"','-r other.txt','example==1\nExample==1'])
def test_direct_declarations_require_unique_exact_pins(text,tmp_path: Path):
    path=tmp_path/'requirements.txt';path.write_text(text,encoding='utf-8')
    with pytest.raises(DependencyError):read_pins(path)


@pytest.mark.parametrize('failure',['none','missing','wrong','unconstrained'])
def test_installed_constraints_and_required_imports(failure,tmp_path: Path):
    (tmp_path/'requirements.txt').write_text('fixture-core==1\n',encoding='utf-8')
    (tmp_path/'constraints-validation.txt').write_text('platform-only==9\n'+('' if failure=='unconstrained' else 'fixture-core==1\n'),encoding='utf-8')
    def lookup(name):
        if name=='platform-only' or failure=='missing':raise PackageNotFoundError(name)
        return '2' if failure=='wrong' else '1'
    if failure=='none':assert checked_versions(tmp_path,('requirements.txt',),lookup)=={'fixture-core':'1'}
    else:
        with pytest.raises(DependencyError):checked_versions(tmp_path,('requirements.txt',),lookup)


@pytest.mark.parametrize('failure',['missing-role','duplicate-role','undeclared-import'])
def test_direct_role_and_import_policy_fails_closed(failure,tmp_path: Path):
    (tmp_path/'tools').mkdir()
    for name in ('requirements-docs.txt','requirements-notebooks.txt','constraints-validation.txt','tools/dependency-policy.json'):shutil.copyfile(ROOT/name,tmp_path/name)
    path=tmp_path/'tools/dependency-policy.json';raw=json.loads(path.read_text(encoding='utf-8'))
    if failure=='missing-role':raw['groups']['site-runtime'].pop()
    elif failure=='duplicate-role':raw['groups']['test-tools'].append(raw['groups']['site-runtime'][0])
    else:(tmp_path/'tools/unreviewed.py').write_text('import not_declared_package\n',encoding='utf-8')
    path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(DependencyError):check_policy(tmp_path)


def test_core_yaml_and_typing_stubs_are_direct_writer_dependencies():
    docs=read_pins(ROOT/'requirements-docs.txt');notebooks=read_pins(ROOT/'requirements-notebooks.txt')
    assert docs['pyyaml']=='6.0.3' and 'pyyaml' not in notebooks
    assert {'types-pyyaml','types-markdown','mypy'}<=docs.keys()
    assert notebooks['numpy']=='2.5.1' and notebooks['scipy']=='1.18.0'

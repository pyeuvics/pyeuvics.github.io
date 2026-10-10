"""Reviewed direct dependency groups and a bounded installed-version constraint check."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

INPUT_FILES=('constraints-validation.txt','requirements-docs.txt','requirements-notebooks.txt','requirements-validation.txt','tools/dependency-policy.json','pyproject.toml')
IMPORTS={'PIL':'pillow','defusedxml':'defusedxml','ipykernel':'ipykernel','jupyter_client':'jupyter-client','markdown':'markdown','mkdocs':'mkdocs','nbclient':'nbclient','nbconvert':'nbconvert','nbformat':'nbformat','packaging':'packaging','pypdf':'pypdf','reportlab':'reportlab','tinycss2':'tinycss2','yaml':'pyyaml','pytest':'pytest'}

class DependencyError(ValueError):
    """Declared pins, dependency roles or installed versions are inconsistent."""


def read_pins(path: Path) -> dict[str,str]:
    pins: dict[str,str]={}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        try:requirement=Requirement(line)
        except ValueError as exc:raise DependencyError('invalid exact dependency declaration') from exc
        name=canonicalize_name(requirement.name);specifiers=list(requirement.specifier)
        if name in pins or len(specifiers)!=1 or specifiers[0].operator!='==' or '*' in specifiers[0].version or requirement.marker or requirement.url or requirement.extras:
            raise DependencyError('dependency declarations require unique exact version pins')
        pins[name]=specifiers[0].version
    return pins


def dependency_inputs(root: Path) -> tuple[str,...]:
    return tuple(name for name in INPUT_FILES if (root/name).is_file())


def checked_versions(root: Path,files: tuple[str,...],lookup: Callable[[str],str]=version) -> dict[str,str]:
    required={}
    for file in files:
        for name,expected in read_pins(root/file).items():
            if name in required:raise DependencyError('duplicate direct dependency declaration')
            required[name]=expected
    constraints=read_pins(root/'constraints-validation.txt')
    if any(constraints.get(name)!=expected for name,expected in required.items()):raise DependencyError('direct pins differ from reviewed constraints')
    installed={}
    for name,expected in constraints.items():
        try:actual=lookup(name)
        except PackageNotFoundError:
            if name in required:raise DependencyError(f'missing declared dependency: {name}')
            continue  # Constraints do not install inactive platform dependencies.
        if actual!=expected:raise DependencyError(f'installed dependency differs from reviewed pin: {name}')
        installed[name]=actual
    return installed


def check_policy(root: Path,mode: str='validation') -> dict[str,str]:
    # Import lazily so notebook consumers can use the pin parser without a package cycle.
    from tools.site_assembly.structured import read_json
    policy=read_json(root/'tools/dependency-policy.json')
    if not isinstance(policy,dict) or set(policy)!={'schema_version','groups'} or type(policy['schema_version']) is not int or policy['schema_version']!=1 or not isinstance(policy['groups'],dict):raise DependencyError('invalid dependency role policy')
    groups=policy['groups']
    if set(groups)!={'site-runtime','notebook-runtime','test-tools','numerical-notebooks'}:raise DependencyError('unexpected dependency role group')
    names: list[str]=[]
    for group in groups.values():
        if not isinstance(group,list) or not group or any(not isinstance(item,str) for item in group):raise DependencyError('invalid dependency role entries')
        names.extend(canonicalize_name(item) for item in group)
    direct={**read_pins(root/'requirements-docs.txt'),**read_pins(root/'requirements-notebooks.txt')}
    if len(set(names))!=len(names) or set(names)!=set(direct):raise DependencyError('direct dependencies do not have exactly one reviewed role')
    for folder in ('tools','tests/support'):
        for path in (root/folder).rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                modules=[alias.name.split('.')[0] for alias in node.names] if isinstance(node,ast.Import) else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.level==0 and node.module else []
                for module in modules:
                    if module in sys.stdlib_module_names or module in {'tools','tests','__future__'}:continue
                    if IMPORTS.get(module) not in direct:raise DependencyError(f'undeclared direct tooling import: {module}')
    if mode not in {'validation','writer'}:raise DependencyError('unsupported dependency mode')
    files=('requirements-docs.txt','requirements-notebooks.txt') if mode=='validation' else ('requirements-docs.txt',)
    return checked_versions(root,files)


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'));parser.add_argument('--mode',choices=['validation','writer'],default='validation');args=parser.parse_args(argv)
    try:
        installed=check_policy(args.root,args.mode)
    except (OSError,ValueError) as exc:
        print(f'dependency policy error: {exc}',file=sys.stderr);return 1
    print(f'dependency policy passed ({args.mode}; {len(installed)} installed constrained packages)')
    return 0

if __name__=='__main__':raise SystemExit(main())

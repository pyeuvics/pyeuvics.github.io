"""Select the intended interpreter and describe its checked execution inputs."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import distribution, version
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any

from jupyter_client.manager import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

from tools.dependencies import DependencyError,checked_versions,dependency_inputs
from .models import NotebookSpec
from .notebook_policy import NotebookError
from .primitives import atomic_write_text, sha256_file
from .structured import read_yaml


@dataclass(frozen=True)
class EnvironmentIdentity:
    python_version: str
    implementation: str
    platform: str
    interpreter_sha256: str
    packages: tuple[tuple[str,str,str], ...]
    requirements: tuple[tuple[str,str], ...]
    source_tree_sha256: str
    source_policies: tuple[tuple[str,str], ...]
    python_hash_seed: str
    execution_policy: tuple[tuple[str,str], ...] = ()

    def to_dict(self) -> dict[str,Any]:
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def validate_source_environments(spec: NotebookSpec, source_root: Path, installed: dict[str,str]) -> tuple[tuple[str,str], ...]:
    policies: list[tuple[str,str]]=[]
    for relative in spec.configurations:
        if Path(relative).name not in {'environment.yaml','environment.yml'}:continue
        path=source_root/relative
        if path.stat().st_size>65_536:raise NotebookError('source environment policy exceeds size limit')
        policy=read_yaml(path)
        if not isinstance(policy,dict) or type(policy.get('schema_version')) is not int or policy['schema_version']!=1:
            raise NotebookError('unsupported source environment policy')
        python=policy.get('python');versions=policy.get('versions')
        if not isinstance(python,str) or not isinstance(versions,dict) or not versions:
            raise NotebookError('incomplete source environment policy')
        if platform.python_version() not in SpecifierSet(python):
            raise NotebookError('Python does not match the locked source environment policy')
        seen: set[str]=set()
        for name,expected in versions.items():
            if not isinstance(name,str) or not isinstance(expected,str):raise NotebookError('invalid source environment version')
            normalized=canonicalize_name(name)
            if normalized in seen:raise NotebookError('duplicate normalized source environment dependency')
            seen.add(normalized)
            actual=spec.package_version if normalized=='pyeuvics' else installed.get(normalized)
            if actual!=expected:raise NotebookError(f'locked source environment mismatch for {normalized}')
        policies.append((relative,sha256_file(path)))
    return tuple(policies)


def capture_environment(spec: NotebookSpec, source_root: Path, source_files: dict[str,str]) -> EnvironmentIdentity:
    try:
        if not re.fullmatch('[0-9]+',spec.random_seed) or not 0<=int(spec.random_seed)<=4_294_967_295:
            raise NotebookError('Python hash seed must be an unsigned 32-bit integer')
        website=Path(__file__).resolve().parents[2]
        pins=checked_versions(website,('requirements-docs.txt','requirements-notebooks.txt'),lookup=version)
        requirements=[(filename,sha256_file(website/filename)) for filename in dependency_inputs(website)]
        policies=validate_source_environments(spec,source_root,pins)
        packages=[]
        for package_name,installed in sorted(pins.items()):
            record=distribution(package_name).read_text('RECORD')
            if record is None:raise NotebookError('execution package lacks an installed file record')
            packages.append((package_name,installed,hashlib.sha256(record.encode('utf-8')).hexdigest()))
        source_hash=hashlib.sha256(json.dumps(source_files,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
        return EnvironmentIdentity(platform.python_version(),platform.python_implementation(),platform.system()+'-'+platform.machine(),sha256_file(Path(sys.executable)),tuple(packages),tuple(requirements),source_hash,policies,spec.random_seed)
    except NotebookError:
        raise
    except DependencyError as exc:
        raise NotebookError(f'website execution environment mismatch: {exc}') from exc
    except Exception as exc:
        raise NotebookError('cannot validate notebook execution environment') from exc


def owned_kernel(runtime_home: Path, launcher: Path | None = None, policy: Path | None = None) -> AsyncKernelManager:
    kernels=runtime_home/'kernels';folder=kernels/'publication';folder.mkdir(parents=True)
    argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'] if launcher is None else [sys.executable,str(launcher),str(policy),'-f','{connection_file}']
    spec={'argv':argv,'display_name':'Publication Python','language':'python'}
    atomic_write_text(folder/'kernel.json',json.dumps(spec,sort_keys=True)+'\n')
    manager=KernelSpecManager(kernel_dirs=[str(kernels)],ensure_native_kernel=False)
    if manager.get_kernel_spec('publication').argv!=spec['argv']:
        raise NotebookError('owned notebook kernel differs from the intended interpreter')
    return AsyncKernelManager(kernel_name='publication',kernel_spec_manager=manager,connection_file=str(runtime_home/'runtime/connection.json'))

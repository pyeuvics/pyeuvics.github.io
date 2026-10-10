"""Secret-free website quality checks shared by local, PR and source-backed runs."""
from __future__ import annotations
import argparse
from collections.abc import Callable
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4
from .site_assembly.primitives import atomic_write_text,run_text
from .site_assembly.promotion import promote_directory
from .site_assembly.structured import read_json
from .site_assembly.timestamps import parse_timestamp
from .validation_evidence import WebsiteIdentity,EnvironmentIdentity,website_identity,environment_identity

TYPING_TARGETS=('tools','tests/support')
QUALITY_CHECKS=('dependency-policy','website-tests','strict-typing','strict-mkdocs')
POLICY='website-source-quality-v2'
Runner=Callable[[list[str],Path,str | None],None]

class QualityError(ValueError):
    """A source-only quality stage failed or its receipt cannot be reused."""


def run_command(arguments: list[str],cwd: Path,epoch: str | None=None) -> None:
    environment=dict(os.environ)
    if epoch is not None:environment['SOURCE_DATE_EPOCH']=epoch
    try:
        subprocess.run(arguments,cwd=cwd,check=True,env=environment)
    except (OSError,subprocess.CalledProcessError) as exc:raise QualityError('website quality command failed') from exc


def run_checks(root: Path,output: Path,epoch: str,runner: Runner=run_command) -> None:
    output.mkdir(parents=True,exist_ok=False)
    commands=[
        [sys.executable,'-m','tools.dependencies'],
        [sys.executable,'-m','pytest'],
        [sys.executable,'-m','mypy','--strict',*TYPING_TARGETS,'--cache-dir',str(output/'mypy-cache')],
        [sys.executable,'-m','mkdocs','build','--strict','--site-dir',str(output/'strict-site')],
    ]
    for command in commands:runner(command,root,epoch)


def receipt_payload(website: WebsiteIdentity | None,environment: EnvironmentIdentity | None,epoch: str) -> dict[str,object]:
    return {'quality_version':1,'policy':POLICY,'website':asdict(website) if website is not None else None,'environment':asdict(environment) if environment is not None else None,'epoch':epoch,'checks':list(QUALITY_CHECKS)}


def write_receipt(path: Path,website: WebsiteIdentity | None,environment: EnvironmentIdentity | None,epoch: str) -> None:
    atomic_write_text(path,json.dumps(receipt_payload(website,environment,epoch),indent=2,sort_keys=True)+'\n')


def verify_receipt(path: Path,website: WebsiteIdentity,environment: EnvironmentIdentity,epoch: str) -> None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>16*1024*1024:raise QualityError('quality receipt is absent or aliased')
        raw=read_json(path)
        expected=json.loads(json.dumps(receipt_payload(website,environment,epoch)))
        if not isinstance(raw,dict) or type(raw.get('quality_version')) is not int or raw!=expected:
            raise QualityError('quality receipt does not bind the same website, environment, time and policy')
    except (OSError,ValueError) as exc:raise QualityError('quality receipt cannot be reused') from exc


def source_only(root: Path,output: Path,epoch: str,bind: bool=False,runner: Runner=run_command) -> Path:
    root=root.resolve();output=output.absolute();epoch=parse_timestamp(epoch).epoch
    if output.exists() or output.is_symlink():raise QualityError('quality output already exists')
    output.parent.mkdir(parents=True,exist_ok=True)
    workspace=Path(tempfile.mkdtemp(prefix='.'+output.name+'.quality-',dir=output.parent))
    try:
        website=website_identity(root) if bind else None
        environment=environment_identity(root) if bind else None
        run_checks(root,workspace/'checks',epoch,runner)
        if bind and (website_identity(root)!=website or environment_identity(root)!=environment):raise QualityError('website or environment changed during quality checks')
        write_receipt(workspace/'quality-record.json',website,environment,epoch)
        promote_directory(workspace,output)
    except Exception as exc:
        atomic_write_text(workspace/'INCOMPLETE.json',json.dumps({'status':'incomplete','error_type':type(exc).__name__})+'\n')
        raise QualityError('source-only quality failed; owned workspace retained') from exc
    return output/'quality-record.json'


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser();parser.add_argument('--website-root',type=Path,default=Path('.'));parser.add_argument('--output',type=Path);parser.add_argument('--bind',action='store_true',help='Require a clean checkout and record reusable website/environment identity');args=parser.parse_args(argv)
    try:
        root=args.website_root.resolve()
        epoch=os.environ.get('SOURCE_DATE_EPOCH') or run_text(['git','show','-s','--format=%ct','HEAD'],root,'website quality timestamp').strip()
        output=args.output or root/'.staging'/('source-quality-'+uuid4().hex[:12])
        record=source_only(root,output,epoch,args.bind)
    except (OSError,ValueError) as exc:
        print(f'website quality error: {exc}',file=sys.stderr);return 1
    print(f'website quality passed; record: {record}')
    return 0

if __name__=='__main__':raise SystemExit(main())

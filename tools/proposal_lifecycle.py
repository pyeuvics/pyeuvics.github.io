"""Explicit proposal writes and pure lifecycle decisions; tests never contact GitHub."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
from typing import Protocol

PREFIX='automation/source-lock-update-'
BRANCH=re.compile(r'automation/source-lock-update-[0-9]+')
SHA=re.compile(r'[0-9a-f]{40}')

class ProposalError(ValueError):
    """A proposal operation failed or its state is ambiguous."""

class Runner(Protocol):
    def __call__(self,arguments: list[str]) -> str: ...

@dataclass(frozen=True)
class PullRequest:
    number: int
    branch: str
    repository: str | None
    state: str
    sha: str
    url: str

@dataclass(frozen=True)
class Gate:
    active: tuple[int,...]
    orphans: tuple[str,...]

    @property
    def proceed(self) -> bool:return not self.active and not self.orphans


def repository_name(value: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value):raise ProposalError('invalid proposal repository')
    return value


def parse_pulls(text: str,repository: str) -> tuple[PullRequest,...]:
    try:
        pages=json.loads(text)
        if not isinstance(pages,list) or not pages or any(not isinstance(page,list) for page in pages):raise ProposalError('invalid paginated pull request response')
        result=[];numbers=set()
        for page in pages:
            for raw in page:
                if not isinstance(raw,dict) or type(raw.get('number')) is not int or raw['number']<=0 or raw['number'] in numbers:raise ProposalError('invalid pull request identity')
                head=raw.get('head');state=raw.get('state')
                if not isinstance(head,dict) or state not in {'open','closed'}:raise ProposalError('invalid pull request state')
                ref=head.get('ref');sha=head.get('sha');repo=head.get('repo')
                if not isinstance(ref,str) or not isinstance(sha,str) or SHA.fullmatch(sha) is None:raise ProposalError('invalid pull request head')
                owner=None if repo is None else repo.get('full_name') if isinstance(repo,dict) else False
                if owner is not None and not isinstance(owner,str):raise ProposalError('invalid pull request repository')
                url=raw.get('html_url')
                if url!=f'https://github.com/{repository}/pull/{raw["number"]}':raise ProposalError('invalid pull request URL')
                numbers.add(raw['number']);result.append(PullRequest(raw['number'],ref,owner,state,sha,url))
        return tuple(result)
    except (KeyError,TypeError,ValueError) as exc:
        raise ProposalError('cannot parse complete pull request state') from exc


def read_pulls(run: Runner,repository: str) -> tuple[PullRequest,...]:
    repository_name(repository)
    return parse_pulls(run(['gh','api','--method','GET','--paginate','--slurp',f'repos/{repository}/pulls?state=all&per_page=100']),repository)


def read_branches(run: Runner) -> dict[str,str]:
    result={}
    for line in run(['git','ls-remote','--heads','origin','refs/heads/'+PREFIX+'*']).splitlines():
        parts=line.split()
        if len(parts)!=2 or SHA.fullmatch(parts[0]) is None or not parts[1].startswith('refs/heads/'+PREFIX):raise ProposalError('invalid proposal branch response')
        name=parts[1].removeprefix('refs/heads/')
        if name in result:raise ProposalError('duplicate proposal branch response')
        result[name]=parts[0]
    return result


def decide_gate(pulls: tuple[PullRequest,...],branches: dict[str,str],repository: str) -> Gate:
    relevant=tuple(item for item in pulls if item.branch.startswith(PREFIX) and (item.repository is None or item.repository.casefold()==repository.casefold()))
    active=tuple(sorted(item.number for item in relevant if item.state=='open'))
    associated={item.branch for item in relevant if item.repository is not None}
    return Gate(active,tuple(sorted(branch for branch in branches if branch not in associated or BRANCH.fullmatch(branch) is None)))


def recovery_action(pulls: tuple[PullRequest,...],branches: dict[str,str],repository: str,branch: str,sha: str) -> tuple[str,str | None]:
    if BRANCH.fullmatch(branch) is None or SHA.fullmatch(sha) is None:raise ProposalError('cleanup requires the exact owned branch and commit')
    if any(item.branch==branch and item.repository is None for item in pulls):return 'retain',None
    associated=[item for item in pulls if item.branch==branch and item.repository is not None and item.repository.casefold()==repository.casefold()]
    if associated:
        if len(associated)==1 and associated[0].sha==sha:return 'preserve',associated[0].url
        return 'retain',None
    if branch not in branches:return 'absent',None
    return ('delete',None) if branches[branch]==sha else ('retain',None)


def recover(run: Runner,repository: str,branch: str,sha: str) -> str | None:
    action,url=recovery_action(read_pulls(run,repository),read_branches(run),repository,branch,sha)
    if action=='retain':raise ProposalError('proposal state changed; branch retained for review')
    if action=='delete':
        run(['git','push',f'--force-with-lease=refs/heads/{branch}:{sha}','origin',f':refs/heads/{branch}'])
    return url


def propose(run: Runner,repository: str,branch: str,body: Path,allow_write: bool) -> str:
    if not allow_write:raise ProposalError('proposal writes require the explicit workflow write interface')
    repository_name(repository)
    if BRANCH.fullmatch(branch) is None:raise ProposalError('invalid owned proposal branch')
    if not decide_gate(read_pulls(run,repository),read_branches(run),repository).proceed:raise ProposalError('an active or orphaned proposal requires review')
    status=run(['git','status','--porcelain=v1','-z'])
    if status=='':return 'no-change'
    if status!=' M sources.lock.yml\0':raise ProposalError('proposal must contain only an unstaged source lock change')
    if not body.is_file() or body.is_symlink():raise ProposalError('proposal body is missing or aliased')
    run(['git','config','user.name','github-actions[bot]'])
    run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'])
    run(['git','checkout','-b',branch])
    run(['git','add','--','sources.lock.yml'])
    message='Propose verified source lock update\n\nUpdates only exact source commits for review.\nPreserves publication manifests and approval requirements.\nRequires normal human review before merge.\n\nFiles:\n M  sources.lock.yml\n'
    run(['git','commit','-m',message])
    sha=run(['git','rev-parse','HEAD']).strip()
    if SHA.fullmatch(sha) is None:raise ProposalError('invalid owned proposal commit')
    try:
        # Create-only lease: never overwrite a branch that appeared after the gate.
        run(['git','push',f'--force-with-lease=refs/heads/{branch}:','--set-upstream','origin',f'HEAD:refs/heads/{branch}'])
        url=run(['gh','pr','create','--repo',repository,'--base','main','--head',branch,'--title','Propose verified source lock update','--body-file',str(body)]).strip()
        if not re.fullmatch(re.escape('https://github.com/'+repository+'/pull/')+r'[0-9]+',url):raise ProposalError('ambiguous pull request creation result')
        return url
    except BaseException as original:
        try:
            recovered=recover(run,repository,branch,sha)
        except BaseException as cleanup:
            raise ProposalError('proposal failed; recovery could not confirm cleanup, so the branch is retained for review') from cleanup
        if recovered is not None and isinstance(original,Exception):return recovered
        raise


class CommandRunner:
    def __init__(self,root: Path) -> None:self.root=root
    def __call__(self,arguments: list[str]) -> str:
        with tempfile.TemporaryFile() as output:
            try:
                result=subprocess.run(arguments,cwd=self.root,stdout=output,stderr=subprocess.DEVNULL,timeout=120,check=False)
                if result.returncode or output.tell()>8*1024*1024:raise ProposalError('proposal command failed or exceeded output limit')
                output.seek(0);return output.read().decode('utf-8')
            except (OSError,subprocess.TimeoutExpired,UnicodeError) as exc:
                raise ProposalError('proposal command could not complete; output withheld') from exc


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['gate','propose']);parser.add_argument('--repository',required=True);parser.add_argument('--root',type=Path,default=Path.cwd());parser.add_argument('--branch');parser.add_argument('--body',type=Path);parser.add_argument('--allow-write',action='store_true');args=parser.parse_args(argv)
    run=CommandRunner(args.root)
    def cancelled(signum: int,frame: object) -> None:raise KeyboardInterrupt('proposal cancelled')
    previous=signal.signal(signal.SIGTERM,cancelled)
    try:
        if args.command=='gate':
            result=decide_gate(read_pulls(run,args.repository),read_branches(run),args.repository)
            print('proceed='+str(result.proceed).lower())
            print('active_count='+str(len(result.active)))
            print('orphan_count='+str(len(result.orphans)))
        else:
            if args.branch is None or args.body is None:raise ProposalError('proposal branch and body are required')
            print(propose(run,args.repository,args.branch,args.body,args.allow_write))
        return 0
    except (ProposalError,KeyboardInterrupt) as exc:
        print(str(exc),file=sys.stderr);return 1
    finally:signal.signal(signal.SIGTERM,previous)

if __name__=='__main__':raise SystemExit(main())

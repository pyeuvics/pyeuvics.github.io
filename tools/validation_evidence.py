"""Validation consistency evidence, not scientific approval or validator authentication."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import distributions
from pathlib import Path
from typing import Any

from .dependencies import dependency_inputs
from .review_manifest import ReviewFile, ReviewManifest, parse_review_manifest
from .site_assembly.contracts import load_locks
from .site_assembly.primitives import atomic_write_text, run_text, sha256_file
from .site_assembly.structured import read_json

CHECKS=('source-contracts','dependency-policy','bounded-lint','website-tests','strict-typing','strict-mkdocs','assembly','artifact-validation','review-manifest')
ARTIFACT_EVIDENCE=('artifact-plan.json','publication-artifact-manifest.json','quality-record.json','staged-content-inventory.json','staging-plan.json')
BUNDLE_FILES=('ancestry.json','baseline/review-artifact-manifest.json','baseline/validation-record.json','candidate/review-artifact-manifest.json','candidate/validation-record.json','proposal/pull-request.md','proposal/pull-request.md.json','proposal/sources.lock.yml')
REQUIREMENTS=('requirements-docs.txt','requirements-notebooks.txt')

class EvidenceError(ValueError):
    """Evidence is absent, inconsistent, stale or malformed."""

@dataclass(frozen=True)
class WebsiteIdentity:
    commit: str
    inputs_sha256: str

@dataclass(frozen=True)
class EnvironmentIdentity:
    python: str
    interpreter_sha256: str
    platform: str
    requirements: tuple[tuple[str,str],...]
    packages: tuple[tuple[str,str],...]
    installed_files_sha256: str

@dataclass(frozen=True)
class LockIdentity:
    sha256: str
    euvics: str
    pyeuvics: str

@dataclass(frozen=True)
class ValidationRecord:
    website: WebsiteIdentity
    environment: EnvironmentIdentity
    lock: LockIdentity
    epoch: str
    checks: tuple[str,...]
    artifact_manifest_sha256: str
    evidence: tuple[tuple[str,str],...]

    def to_dict(self) -> dict[str,object]:return {'validation_version':1,**asdict(self)}


def _json_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def website_identity(root: Path) -> WebsiteIdentity:
    """Bind all tracked bytes, including assume-unchanged files, to one commit."""
    root=root.resolve()
    if run_text(['git','status','--porcelain','--untracked-files=all'],root,'website cleanliness').strip():raise EvidenceError('validation evidence requires a clean website checkout')
    commit=run_text(['git','rev-parse','HEAD'],root,'website revision').strip()
    if re.fullmatch('[0-9a-f]{40}',commit) is None:raise EvidenceError('invalid website revision')
    records=[]
    tree=run_text(['git','ls-tree','-rz',commit],root,'website input tree').split('\0')
    tracked={record.split('\t',1)[1] for record in tree if record}
    aliases={'CLAUDE.md':'AGENTS.md','content/stylesheets/readthedocs.css':'docs/stylesheets/readthedocs.css'}
    for record in tree:
        if not record:continue
        metadata,name=record.split('\t',1);mode,kind,oid=metadata.split();path=root/name
        if kind!='blob' or mode not in {'100644','100755','120000'}:raise EvidenceError('unsupported website input object')
        if mode=='120000':
            target=aliases.get(name)
            if target is None or target not in tracked or not path.is_symlink() or path.resolve()!=root/target or not (root/target).is_file() or (root/target).is_symlink():raise EvidenceError('unapproved website input alias')
            content=os.readlink(path).encode('utf-8');actual=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest();digest=hashlib.sha256(content).hexdigest()
        else:
            if path.is_symlink() or not path.is_file() or any(parent.is_symlink() for parent in path.parents if parent!=root and root in parent.parents):raise EvidenceError('aliased or missing website input')
            actual=run_text(['git','hash-object','--no-filters','--',name],root,'website input bytes').strip();digest=sha256_file(path)
        if actual!=oid:raise EvidenceError('website input bytes differ from the recorded revision')
        records.append((name,digest))
    return WebsiteIdentity(commit,_json_hash(records))


def requirement_identity(root: Path) -> tuple[tuple[str,str],...]:
    return tuple((name,sha256_file(root/name)) for name in dependency_inputs(root))


def environment_identity(root: Path) -> EnvironmentIdentity:
    """Fingerprint installed files; generated Python caches are not runtime inputs."""
    packages=[];files=[];prefix=Path(sys.prefix).resolve()
    for dist in distributions():
        name=dist.metadata['Name'].lower().replace('_','-');packages.append((name,dist.version))
        if dist.files is None:raise EvidenceError('installed distribution lacks a file inventory')
        for entry in dist.files:
            if str(entry).endswith('.pyc'):continue
            path=Path(str(dist.locate_file(entry)))
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(prefix):raise EvidenceError('installed environment contains an untracked or aliased distribution file')
            files.append((name,str(entry),sha256_file(path)))
    if len({name for name,_ in packages})!=len(packages):raise EvidenceError('ambiguous installed package identity')
    return EnvironmentIdentity(platform.python_version(),sha256_file(Path(sys.executable)),sys.platform+'/'+platform.machine(),requirement_identity(root),tuple(sorted(packages)),_json_hash(sorted(files)))


def lock_identity(path: Path) -> LockIdentity:
    locks=load_locks(path)
    return LockIdentity(sha256_file(path),locks['euvics'].commit,locks['pyeuvics'].commit)


def _object(value: object,fields: set[str]) -> dict[str,Any]:
    if not isinstance(value,dict) or set(value)!=fields:raise EvidenceError('invalid evidence object fields')
    return value


def _digest(value: object,length: int=64) -> str:
    if not isinstance(value,str) or re.fullmatch('[0-9a-f]{'+str(length)+'}',value) is None:raise EvidenceError('invalid evidence digest')
    return value


def _text(value: object) -> str:
    if not isinstance(value,str) or not value or any(ord(c)<32 for c in value):raise EvidenceError('invalid evidence text')
    return value


def _pairs(value: object,*,digests: bool=False) -> tuple[tuple[str,str],...]:
    if not isinstance(value,list):raise EvidenceError('invalid evidence sequence')
    result=[]
    for item in value:
        if not isinstance(item,list) or len(item)!=2:raise EvidenceError('invalid evidence pair')
        result.append((_text(item[0]),_digest(item[1]) if digests else _text(item[1])))
    if result!=sorted(result) or len({name for name,_ in result})!=len(result):raise EvidenceError('ambiguous or unordered evidence sequence')
    return tuple(result)


def _read(path: Path) -> object:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>16*1024*1024:raise EvidenceError('evidence file is missing, aliased or too large')
        return read_json(path)
    except (OSError,ValueError,RecursionError) as exc:raise EvidenceError('cannot read valid evidence') from exc


def read_record(path: Path) -> ValidationRecord:
    raw=_object(_read(path),{'validation_version','website','environment','lock','epoch','checks','artifact_manifest_sha256','evidence'})
    if type(raw['validation_version']) is not int or raw['validation_version']!=1:raise EvidenceError('unsupported validation record version')
    website=_object(raw['website'],{'commit','inputs_sha256'});env=_object(raw['environment'],{'python','interpreter_sha256','platform','requirements','packages','installed_files_sha256'});lock=_object(raw['lock'],{'sha256','euvics','pyeuvics'})
    if raw['checks']!=list(CHECKS) or not isinstance(raw['epoch'],str) or re.fullmatch('0|[1-9][0-9]*',raw['epoch']) is None:raise EvidenceError('incomplete checks or invalid epoch')
    evidence=_pairs(raw['evidence'],digests=True)
    if not set(ARTIFACT_EVIDENCE).issubset(dict(evidence)):raise EvidenceError('incomplete artifact ownership evidence')
    return ValidationRecord(WebsiteIdentity(_digest(website['commit'],40),_digest(website['inputs_sha256'])),EnvironmentIdentity(_text(env['python']),_digest(env['interpreter_sha256']),_text(env['platform']),_pairs(env['requirements'],digests=True),_pairs(env['packages']),_digest(env['installed_files_sha256'])),LockIdentity(_digest(lock['sha256']),_digest(lock['euvics'],40),_digest(lock['pyeuvics'],40)),raw['epoch'],CHECKS,_digest(raw['artifact_manifest_sha256']),evidence)


def write_record(path: Path,website: WebsiteIdentity,environment: EnvironmentIdentity,lock: LockIdentity,epoch: str) -> None:
    root=path.parent
    names=list(ARTIFACT_EVIDENCE)
    for name in ('notebook-execution-provenance.json','source-build/document-build-evidence.json'):
        if (root/name).exists():names.append(name)
    record=ValidationRecord(website,environment,lock,epoch,CHECKS,sha256_file(root/'review-artifact-manifest.json'),tuple((name,sha256_file(root/name)) for name in sorted(names)))
    atomic_write_text(path,json.dumps(record.to_dict(),indent=2,sort_keys=True)+'\n')
    read_record(path)


def write_ancestry(path: Path,current: Path,candidate: Path) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_text(path,json.dumps({'ancestry_version':1,'current':asdict(lock_identity(current)),'candidate':asdict(lock_identity(candidate))},indent=2,sort_keys=True)+'\n')


def validate_pair(root: Path,website: Path,current: Path,candidate: Path) -> None:
    if sha256_file(root/'proposal/sources.lock.yml')!=sha256_file(candidate):raise EvidenceError('candidate lock package differs')
    baseline=read_record(root/'baseline/validation-record.json');proposed=read_record(root/'candidate/validation-record.json')
    identity=website_identity(website)
    if baseline.website!=identity or proposed.website!=identity:raise EvidenceError('validation website revision or inputs are stale')
    if baseline.environment!=proposed.environment or baseline.environment.requirements!=requirement_identity(website):raise EvidenceError('validation environments or requirements differ')
    if baseline.epoch!=proposed.epoch:raise EvidenceError('validation timestamps differ')
    if baseline.lock!=lock_identity(current) or proposed.lock!=lock_identity(candidate):raise EvidenceError('validation source locks differ')
    for folder,record in [('baseline',baseline),('candidate',proposed)]:
        manifest=root/folder/'review-artifact-manifest.json'
        parsed=parse_review_manifest(_read(manifest))
        if sha256_file(manifest)!=record.artifact_manifest_sha256:raise EvidenceError('review artifact manifest was changed')
        recorded=parsed.by_path()
        for name,digest in record.evidence:
            if name not in recorded or recorded[name].sha256!=digest:raise EvidenceError('artifact ownership evidence is not bound by the review manifest')
    ancestry=_read(root/'ancestry.json')
    expected={'ancestry_version':1,'current':asdict(lock_identity(current)),'candidate':asdict(lock_identity(candidate))}
    if ancestry!=expected or not isinstance(ancestry,dict) or type(ancestry.get('ancestry_version')) is not int:raise EvidenceError('source ancestry evidence differs')


def _bundle_manifest(root: Path) -> ReviewManifest:
    files=[]
    for name in BUNDLE_FILES:
        path=root/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise EvidenceError('proposal evidence file is missing or aliased')
        files.append(ReviewFile(name,sha256_file(path),path.stat().st_size))
    return ReviewManifest(tuple(files))


def write_bundle(root: Path,website: Path,current: Path,candidate: Path) -> None:
    validate_pair(root,website,current,candidate)
    data=_bundle_manifest(root).to_dict();data['evidence_version']=data.pop('manifest_version')
    atomic_write_text(root/'proposal/validation-evidence.json',json.dumps(data,indent=2,sort_keys=True)+'\n')


def verify_bundle(root: Path,website: Path,current: Path,candidate: Path) -> None:
    raw=_object(_read(root/'proposal/validation-evidence.json'),{'evidence_version','files'})
    declared=parse_review_manifest({'manifest_version':raw['evidence_version'],'files':raw['files']})
    if declared!=_bundle_manifest(root):raise EvidenceError('proposal evidence package was changed or mixed')
    validate_pair(root,website,current,candidate)

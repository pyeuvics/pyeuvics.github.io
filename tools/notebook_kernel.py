"""Trusted notebook bootstrap with narrow Python source/data/process guards.

This is not a security sandbox: native I/O, global filesystem access and network
access are not isolated. Only reviewed locked source code may execute here.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable


def source_guard(source: Path, allowed: frozenset[str]) -> Callable[[str, tuple[Any, ...]], None]:
    root=source.resolve()
    process_events={'subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.posix_spawnp','os.exec','os.spawn','os.startfile','os.startfile/2','_winapi.CreateProcess','pty.spawn'}
    mutation_events={'os.remove','os.rmdir','os.mkdir','os.chmod','os.chown','os.utime','os.truncate','os.symlink','os.link','os.rename'}
    def source_path(value: Any) -> str | None:
        if not isinstance(value,(str,bytes,os.PathLike)):return None
        path=Path(os.fsdecode(value)).resolve()
        try:return path.relative_to(root).as_posix()
        except ValueError:return None
    def audit(event: str,args: tuple[Any,...]) -> None:
        if event in process_events:
            raise PermissionError('unmanaged notebook child processes are unsupported')
        if event in mutation_events:
            paths=args[:2] if event in {'os.symlink','os.link','os.rename'} else args[:1]
            if any(source_path(path) is not None for path in paths):
                raise PermissionError('notebook source writes are forbidden')
        if event!='open' or not args:return
        relative=source_path(args[0])
        if relative is None:return
        mode=args[1] if len(args)>1 else None
        flags=args[2] if len(args)>2 else 0
        writing=(isinstance(mode,str) and any(value in mode for value in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing:raise PermissionError('notebook source writes are forbidden')
        if relative not in allowed and Path(relative).suffix not in {'.py','.pyi'}:
            raise PermissionError('notebook read an undeclared source data file')
    return audit


def main() -> None:
    if sys.implementation.name!='cpython' or not hasattr(sys,'addaudithook'):
        raise RuntimeError('required notebook audit events are unavailable')
    policy=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if policy.get('version')!=1:raise RuntimeError('unsupported notebook guard policy')
    sys.argv=[sys.argv[0],*sys.argv[2:]]
    from ipykernel.kernelapp import IPKernelApp
    app=IPKernelApp.instance()
    app.initialize()  # type: ignore[no-untyped-call]  # ipykernel lifecycle API lacks annotations.
    sys.addaudithook(source_guard(Path(policy['source_root']),frozenset(policy['allowed_source_files'])))
    app.start()  # type: ignore[no-untyped-call]  # ipykernel lifecycle API lacks annotations.


if __name__=='__main__':main()

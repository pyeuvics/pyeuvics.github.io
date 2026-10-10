"""Accumulation/observation budgets and deterministic kernel cleanup."""
from __future__ import annotations
import asyncio
import atexit
from dataclasses import asdict, dataclass
import json
import math
import os
import stat
from pathlib import Path
from typing import Any

from jupyter_client.manager import AsyncKernelManager
from nbclient import NotebookClient
from nbformat import NotebookNode
from .models import NotebookSpec
from .notebook_policy import NotebookError
from .primitives import atomic_write_text


@dataclass(frozen=True)
class ExecutionLimits:
    total_seconds: float = 300
    cell_seconds: int = 120
    max_cells: int = 500
    max_messages: int = 10_000
    max_output_bytes: int = 16_777_216
    max_runtime_entries: int = 512
    max_runtime_bytes: int = 33_554_432

    def validate(self) -> None:
        if type(self.total_seconds) not in (int,float) or not math.isfinite(self.total_seconds) or self.total_seconds<=0:
            raise NotebookError('invalid notebook total-time budget')
        for name,value in asdict(self).items():
            if name!='total_seconds' and (type(value) is not int or value<=0):
                raise NotebookError('invalid notebook resource budget')

    @classmethod
    def for_notebook(cls,spec: NotebookSpec) -> ExecutionLimits:
        return cls(max_output_bytes=min(16_777_216,max(65_536,spec.max_rendered_bytes*3)))


def inspect_runtime(roots: tuple[Path,...], limits: ExecutionLimits) -> None:
    pending=list(roots);entries=0;size=0
    while pending:
        root=pending.pop()
        if root.is_symlink():raise NotebookError('notebook runtime directory is aliased')
        try:children=os.scandir(root)
        except FileNotFoundError:
            if root in roots:raise NotebookError('notebook runtime directory is missing') from None
            continue  # Temporary subdirectories may disappear between polls.
        with children:
            for entry in children:
                try:info=entry.stat(follow_symlinks=False)
                except FileNotFoundError:continue
                entries+=1
                if entries>limits.max_runtime_entries:raise NotebookError('notebook runtime entry limit exceeded')
                if stat.S_ISDIR(info.st_mode):pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    size+=info.st_size
                    if size>limits.max_runtime_bytes:raise NotebookError('notebook runtime byte limit exceeded')
                else:raise NotebookError('notebook runtime contains an aliased or nonregular file')


class BoundedNotebookClient(NotebookClient):
    def __init__(self,nb: NotebookNode,*,limits: ExecutionLimits,receipt: Path,**kwargs: Any) -> None:
        self.limits=limits;self.receipt=receipt
        self.message_bytes=0;self.message_count=0
        self.budget_error: NotebookError | None = None
        super().__init__(nb,**kwargs)

    async def async_start_new_kernel(self,**kwargs: Any) -> None:
        await super().async_start_new_kernel(**kwargs)
        assert self.km is not None
        pid=getattr(self.km.provisioner,'pid',None)
        if type(pid) is not int or pid<=0:raise NotebookError('owned kernel process identity is unavailable')
        atomic_write_text(self.receipt,json.dumps({'pid':pid})+'\n')

    def process_message(self,msg: dict[str,Any],cell: NotebookNode,cell_index: int) -> NotebookNode | None:
        self.message_count+=1
        self.message_bytes+=len(json.dumps(msg.get('content',{}),ensure_ascii=False).encode('utf-8'))
        self.message_bytes+=sum(len(buffer) for buffer in msg.get('buffers',[]))
        if self.message_count>self.limits.max_messages or self.message_bytes>self.limits.max_output_bytes:
            self.budget_error=NotebookError('notebook accumulated output/message limit exceeded')
            raise self.budget_error
        return super().process_message(msg,cell,cell_index)


async def execute_bounded(client: BoundedNotebookClient,manager: AsyncKernelManager,source_root: Path,
                          environment: dict[str,str],runtime_roots: tuple[Path,...]) -> NotebookNode:
    async def monitor() -> None:
        while True:
            if client.budget_error is not None:raise client.budget_error
            inspect_runtime(runtime_roots,client.limits)
            await asyncio.sleep(0.05)
    execution=asyncio.create_task(client.async_execute(cwd=str(source_root),env=environment,cleanup_kc=True))
    watching=asyncio.create_task(monitor())
    try:
        done,_=await asyncio.wait((execution,watching),timeout=client.limits.total_seconds,return_when=asyncio.FIRST_COMPLETED)
        if not done:raise NotebookError('notebook total execution time limit exceeded')
        if watching in done:
            watching.result()
            raise NotebookError('notebook resource monitor stopped unexpectedly')
        result=execution.result()
        if client.budget_error is not None:raise client.budget_error
        inspect_runtime(runtime_roots,client.limits)
        return result
    finally:
        execution.cancel();watching.cancel()
        await asyncio.gather(execution,watching,return_exceptions=True)
        cleanup=getattr(client,'_async_cleanup_kernel_future',None)
        if cleanup is not None:await asyncio.gather(cleanup,return_exceptions=True)
        try:
            if manager.has_kernel:await manager.shutdown_kernel(now=True)
        finally:
            await manager.cleanup_resources()
            client.receipt.unlink(missing_ok=True)
            # nbclient registers before startup; cancellation there can bypass
            # its own unregister path even after explicit cleanup succeeds.
            atexit.unregister(client._cleanup_kernel)

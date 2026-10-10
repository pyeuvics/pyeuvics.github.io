"""Real notebook execution and temporary source immutability checks."""
from __future__ import annotations
import os
import asyncio
from dataclasses import asdict, replace
import json
import shutil
import stat
from pathlib import Path
from .notebook_environment import capture_environment, owned_kernel
from .primitives import atomic_write_text, sha256_file as _sha256
from .notebook_limits import ExecutionLimits, BoundedNotebookClient, execute_bounded
from .notebook_policy import AdmittedNotebook, ExecutedNotebook, INHERITED_ENVIRONMENT, NotebookError

def _tree_snapshot(root: Path) -> dict[str, str]:
    result: dict[str,str] = {}
    for path in root.rglob('*'):
        mode=path.stat(follow_symlinks=False).st_mode
        relative=path.relative_to(root).as_posix()
        if stat.S_ISREG(mode):result[relative]=_sha256(path)
        elif stat.S_ISDIR(mode):result[relative+'/']='directory'
        else:raise NotebookError('notebook source contains an aliased or nonregular entry')
    return result


async def execute_notebook_async(admitted: AdmittedNotebook, limits: ExecutionLimits | None = None) -> ExecutedNotebook:
    spec, source_root, notebook = admitted.spec, admitted.source_root, admitted.notebook
    limits=limits or ExecutionLimits.for_notebook(spec)
    limits.validate()
    if len(notebook.cells)>limits.max_cells:raise NotebookError('notebook cell count limit exceeded')
    before = _tree_snapshot(source_root)
    identity = capture_environment(spec,source_root,before)
    runtime_parent = source_root.parent / "notebook-runtime-output"
    runtime_output = runtime_parent / Path(spec.path).stem
    runtime_output.mkdir(parents=True,exist_ok=False)
    runtime_home = source_root.parent / "notebook-runtime-home"
    runtime_home.mkdir(exist_ok=False)
    environment = {
        name: value
        for name in INHERITED_ENVIRONMENT
        if (value := os.environ.get(name)) is not None
    }
    environment.update(
        {
            "HOME": str(runtime_home),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "MPLBACKEND": "Agg",
            "PYEUVICS_NOTEBOOK_OUTPUT": (
                f"../notebook-runtime-output/{Path(spec.path).stem}"
            ),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": spec.random_seed,
            "TZ": "UTC",
        }
    )
    for variable,folder in {'JUPYTER_CONFIG_DIR':'config','JUPYTER_DATA_DIR':'data','JUPYTER_RUNTIME_DIR':'runtime','IPYTHONDIR':'ipython','MPLCONFIGDIR':'matplotlib','TMPDIR':'tmp'}.items():
        directory=runtime_home/folder;directory.mkdir()
        environment[variable]=str(directory)
    environment['TEMP']=environment['TMP']=environment['TMPDIR']
    launcher=runtime_home/'kernel-launcher.py'
    shutil.copyfile(Path(__file__).resolve().parents[1]/'notebook_kernel.py',launcher)
    policy=runtime_home/'source-policy.json'
    atomic_write_text(policy,json.dumps({'version':1,'source_root':str(source_root),'allowed_source_files':sorted({spec.path,*spec.dependencies,*spec.configurations})})+'\n')
    identity=replace(identity,execution_policy=(('trust_model','reviewed-locked-source'),('guard_sha256',_sha256(launcher)),('limits',json.dumps(asdict(limits),sort_keys=True))))
    source_path = source_root / "src"
    if source_path.is_dir():
        environment["PYTHONPATH"] = str(source_path)
    manager=owned_kernel(runtime_home,launcher,policy)
    client = BoundedNotebookClient(
        notebook,
        limits=limits,
        receipt=runtime_home/'kernel-process.json',
        timeout=limits.cell_seconds,
        km=manager,
        kernel_name="publication",
        allow_errors=False,
        record_timing=False,
        force_raise_errors=True,
        shutdown_kernel="immediate",
        raise_on_iopub_timeout=True,
    )
    try:
        executed = await execute_bounded(client,manager,source_root,environment,(runtime_home,runtime_output))
    except NotebookError:
        raise
    except Exception as exc:
        raise NotebookError(f"notebook execution failed: {spec.path}") from exc
    after = _tree_snapshot(source_root)
    if after != before:
        raise NotebookError(f"notebook execution modified its temporary source tree: {spec.path}")
    return ExecutedNotebook(spec,executed,identity)


def execute_notebook(admitted: AdmittedNotebook, limits: ExecutionLimits | None = None) -> ExecutedNotebook:
    try:asyncio.get_running_loop()
    except RuntimeError:pass
    else:raise NotebookError('use async notebook execution within an existing event loop')
    return asyncio.run(execute_notebook_async(admitted,limits))

"""Real notebook execution and temporary source immutability checks."""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from .notebook_environment import capture_environment, owned_kernel
from .primitives import sha256_file as _sha256
from .notebook_policy import AdmittedNotebook, ExecutedNotebook, INHERITED_ENVIRONMENT, NotebookError

def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def execute_notebook(admitted: AdmittedNotebook) -> ExecutedNotebook:
    spec, source_root, notebook = admitted.spec, admitted.source_root, admitted.notebook
    before = _tree_snapshot(source_root)
    identity = capture_environment(spec,source_root,before)
    runtime_parent = source_root.parent / "notebook-runtime-output"
    runtime_output = runtime_parent / Path(spec.path).stem
    if runtime_output.exists():
        shutil.rmtree(runtime_output)
    runtime_output.mkdir(parents=True)
    runtime_home = source_root.parent / "notebook-runtime-home"
    if runtime_home.exists():
        shutil.rmtree(runtime_home)
    runtime_home.mkdir()
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
    for variable,folder in {'JUPYTER_CONFIG_DIR':'config','JUPYTER_DATA_DIR':'data','JUPYTER_RUNTIME_DIR':'runtime','IPYTHONDIR':'ipython','MPLCONFIGDIR':'matplotlib'}.items():
        directory=runtime_home/folder;directory.mkdir()
        environment[variable]=str(directory)
    source_path = source_root / "src"
    if source_path.is_dir():
        environment["PYTHONPATH"] = str(source_path)
    client = NotebookClient(
        notebook,
        timeout=120,
        km=owned_kernel(runtime_home),
        kernel_name="publication",
        allow_errors=False,
        record_timing=False,
    )
    try:
        executed = client.execute(cwd=str(source_root), env=environment, cleanup_kc=True)
    except (CellExecutionError, TimeoutError, RuntimeError, OSError) as exc:
        raise NotebookError(f"notebook execution failed: {spec.path}: {exc}") from exc
    after = _tree_snapshot(source_root)
    if after != before:
        raise NotebookError(f"notebook execution modified its temporary source tree: {spec.path}")
    return ExecutedNotebook(spec,executed,identity)

"""Real kernels enforce budgets and are reaped after failures and cancellation."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import time
import nbformat
import pytest
from tests.support.publication import notebook_spec
from tools.site_assembly.notebook_admission import admit_notebook
from tools.site_assembly.notebook_execution import execute_notebook,execute_notebook_async
from tools.site_assembly.notebook_limits import ExecutionLimits
from tools.site_assembly.notebook_policy import NotebookError


def admitted(tmp_path: Path,code: str):
    source=tmp_path/'source';source.mkdir()
    notebook=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(code)])
    (source/'fixture.ipynb').write_text(nbformat.writes(notebook),encoding='utf-8')
    (source/'secret.csv').write_text('excluded-fixture-value',encoding='utf-8')
    return admit_notebook(notebook_spec(),source)


def assert_cleaned(tmp_path: Path) -> None:
    assert not list(tmp_path.rglob('connection.json'))
    assert not list(tmp_path.rglob('kernel-process.json'))


@pytest.mark.parametrize(('code','message','limits'),[
    ("import time\nwhile True: time.sleep(0.1)",'total execution time',ExecutionLimits(total_seconds=4)),
    ("print('x'*200000)",'accumulated output',ExecutionLimits(total_seconds=15,max_output_bytes=10000)),
    ("print('partial fixture')\nraise RuntimeError('private-error-fixture')",'execution failed',ExecutionLimits(total_seconds=15)),
    ("from pathlib import Path\nname='secret'+'.'+'csv'\nprint(Path(name).read_text())",'execution failed',ExecutionLimits(total_seconds=15)),
    ("from pathlib import Path\nPath('changed.py').write_text('changed')",'execution failed',ExecutionLimits(total_seconds=15)),
    ('import subprocess,sys\nsubprocess.run([sys.executable,\'-c\',"from pathlib import Path; Path(\'child-started\').write_text(\'child\')"],check=True)','execution failed',ExecutionLimits(total_seconds=15)),
    ("import os\nfrom pathlib import Path\n(Path(os.environ['PYEUVICS_NOTEBOOK_OUTPUT'])/'large.bin').write_bytes(b'x'*2000000)",'runtime byte limit',ExecutionLimits(total_seconds=15,max_runtime_bytes=300000)),
])
def test_real_failure_paths_cleanup_kernel(code: str,message: str,limits: ExecutionLimits,tmp_path: Path) -> None:
    notebook=admitted(tmp_path,code)
    before=(tmp_path/'source/fixture.ipynb').read_bytes()
    with pytest.raises(NotebookError,match=message) as caught:
        execute_notebook(notebook,limits)
    assert 'private-error-fixture' not in str(caught.value)
    assert 'excluded-fixture-value' not in str(caught.value)
    assert (tmp_path/'source/fixture.ipynb').read_bytes()==before
    assert not (tmp_path/'source/changed.py').exists()
    assert not (tmp_path/'source/child-started').exists()
    assert_cleaned(tmp_path)


def test_real_cancellation_reaps_the_owned_kernel(tmp_path: Path,monkeypatch) -> None:
    import atexit
    from tools.site_assembly.notebook_limits import BoundedNotebookClient
    registered=set();original_register=atexit.register;original_unregister=atexit.unregister
    def register(callback,*args,**kwargs):
        if isinstance(getattr(callback,'__self__',None),BoundedNotebookClient):registered.add(callback)
        return original_register(callback,*args,**kwargs)
    def unregister(callback):
        registered.discard(callback)
        return original_unregister(callback)
    monkeypatch.setattr(atexit,'register',register)
    monkeypatch.setattr(atexit,'unregister',unregister)
    notebook=admitted(tmp_path,"import time\nwhile True: time.sleep(0.1)")
    async def cancel_running() -> int:
        task=asyncio.create_task(execute_notebook_async(notebook,ExecutionLimits(total_seconds=20)))
        receipt=tmp_path/'notebook-runtime-home/kernel-process.json'
        try:
            deadline=time.monotonic()+15
            while not receipt.exists():
                if task.done():await task
                if time.monotonic()>deadline:pytest.fail('owned kernel did not start')
                await asyncio.sleep(0.05)
            pid=json.loads(receipt.read_text(encoding='utf-8'))['pid']
            task.cancel()
            with pytest.raises(asyncio.CancelledError):await task
            return pid
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task,return_exceptions=True)
    pid=asyncio.run(cancel_running())
    assert_cleaned(tmp_path)
    assert not registered
    if os.name=='posix':
        with pytest.raises(ProcessLookupError):os.kill(pid,0)


def test_expected_error_tag_cannot_allow_partial_success(tmp_path: Path) -> None:
    notebook=admitted(tmp_path,"raise RuntimeError('fixture failure')")
    notebook.notebook.cells[0].metadata['tags']=['raises-exception']
    with pytest.raises(NotebookError,match='execution failed'):
        execute_notebook(notebook,ExecutionLimits(total_seconds=15))
    assert_cleaned(tmp_path)


def test_reviewed_matplotlib_plot_still_executes_with_owned_caches(tmp_path: Path) -> None:
    notebook=admitted(tmp_path,"import matplotlib.pyplot as plt\nplt.plot([0,1],[0,1])\nplt.show()")
    result=execute_notebook(notebook,ExecutionLimits(total_seconds=30))
    assert result.environment is not None
    assert_cleaned(tmp_path)

"""Budget and Python-event checks are policy mechanisms, not a sandbox claim."""
from dataclasses import replace
import os
from pathlib import Path
import pytest
from tools.notebook_kernel import source_guard
from tools.site_assembly.notebook_limits import ExecutionLimits,inspect_runtime
from tools.site_assembly.notebook_policy import NotebookError


@pytest.mark.parametrize('change',[{'total_seconds':float('inf')},{'total_seconds':0},{'max_messages':True},{'max_runtime_bytes':-1}])
def test_invalid_limits_fail_closed(change: dict) -> None:
    with pytest.raises(NotebookError):replace(ExecutionLimits(),**change).validate()


@pytest.mark.parametrize('damage',['bytes','entries','symlink'])
def test_owned_runtime_budget(damage: str,tmp_path: Path) -> None:
    if damage=='bytes':(tmp_path/'large').write_bytes(b'x'*101)
    elif damage=='entries':
        for i in range(3):(tmp_path/str(i)).write_bytes(b'')
    else:(tmp_path/'alias').symlink_to('missing')
    with pytest.raises(NotebookError):inspect_runtime((tmp_path,),ExecutionLimits(max_runtime_bytes=100,max_runtime_entries=2))


@pytest.mark.parametrize('event',['subprocess.Popen','os.system','os.fork','os.posix_spawn','os.spawn','os.startfile','pty.spawn'])
def test_unmanaged_python_process_events_are_rejected(event: str,tmp_path: Path) -> None:
    with pytest.raises(PermissionError,match='child processes'):source_guard(tmp_path,frozenset())(event,())


def test_source_guard_accepts_declared_data_and_code_but_rejects_other_reads_and_writes(tmp_path: Path) -> None:
    audit=source_guard(tmp_path,frozenset({'approved.csv'}))
    audit('open',(str(tmp_path/'approved.csv'),'r',os.O_RDONLY))
    audit('open',(str(tmp_path/'src/model.py'),'r',os.O_RDONLY))
    with pytest.raises(PermissionError,match='undeclared'):
        audit('open',(str(tmp_path/'unlisted.csv'),'r',os.O_RDONLY))
    with pytest.raises(PermissionError,match='source writes'):
        audit('open',(str(tmp_path/'approved.csv'),'w',os.O_WRONLY))


def test_skipped_cells_are_rejected_and_cell_count_is_bounded(tmp_path: Path) -> None:
    import nbformat
    from tests.support.publication import notebook_spec
    from tools.site_assembly.notebook_admission import admit_notebook
    from tools.site_assembly.notebook_execution import execute_notebook
    cell=nbformat.v4.new_code_cell('pass',metadata={'tags':['skip-execution']})
    path=tmp_path/'fixture.ipynb'
    path.write_text(nbformat.writes(nbformat.v4.new_notebook(cells=[cell])),encoding='utf-8')
    with pytest.raises(NotebookError,match='skip execution'):admit_notebook(notebook_spec(),tmp_path)
    cell.metadata={}
    path.write_text(nbformat.writes(nbformat.v4.new_notebook(cells=[cell,nbformat.v4.new_code_cell('pass')])),encoding='utf-8')
    with pytest.raises(NotebookError,match='cell count'):
        execute_notebook(admit_notebook(notebook_spec(),tmp_path),ExecutionLimits(max_cells=1))

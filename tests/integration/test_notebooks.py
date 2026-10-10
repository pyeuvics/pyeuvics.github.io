from __future__ import annotations

from pathlib import Path

import pytest

from tools.site_assembly import AssemblyError, assemble_site

from tests.support.publication import (
    create_sources,
    add_approved_notebook_set,
    write_locks,
    snapshot,
)

from tests.support.paths import ROOT


def test_approved_notebook_is_executed_deterministically_and_source_is_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    code = (
        "from pathlib import Path\n"
        "from IPython.display import Image, display\n"
        "import base64\n"
        "print('seed=17', Path('configs/fixture.yaml').read_text().strip())\n"
        "display(Image(data=base64.b64decode("
        "'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='"
        "), format='png'))\n"
    )
    index = pyeuvics / "docs/index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + '\n[Notebook][nb]\n\n[nb]: ../notebooks/00_environment_check.ipynb\n'
        + '<a href="../notebooks/00_environment_check.ipynb">Notebook HTML</a>\n',
        encoding="utf-8",
    )
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code)
    before = snapshot(pyeuvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    first = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-a")
    second = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-b")
    assert snapshot(pyeuvics) == before
    imported = (first.site / "imported/pyeuvics/docs/index.html").read_text(encoding="utf-8")
    assert imported.count('href="../../../software/notebooks/00_environment_check/"') == 2

    page = first.staged_content / "software/notebooks/00_environment_check.md"
    text = page.read_text(encoding="utf-8")
    assert "Static notebook rendering" in text
    assert "Executed during this website build" in text
    assert "synthetic-workflow-check-only" in text
    assert commits["pyeuvics"] in text
    assert "seed=17 fixture: true" in text
    assets = list(
        (first.staged_content / "software/notebooks/00_environment_check_files").glob("*.png")
    )
    assert len(assets) == 1
    final_page = first.site / "software/notebooks/00_environment_check/index.html"
    assert final_page.is_file()
    assert final_page.read_text(encoding="utf-8").count("<h1") == 1
    assert (first.output_root / "staged-content-inventory.json").read_bytes() == (
        second.output_root / "staged-content-inventory.json"
    ).read_bytes()


def test_approved_notebook_writes_only_to_isolated_runtime_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    code = (
        "import os\n"
        "from pathlib import Path\n"
        "output = Path(os.environ['PYEUVICS_NOTEBOOK_OUTPUT'])\n"
        "output.mkdir(parents=True, exist_ok=True)\n"
        "(output / 'status.txt').write_text('ok\\n', encoding='utf-8')\n"
        "print(output.as_posix(), (output / 'status.txt').read_text().strip())\n"
        "print('token=' + os.environ.get('GITHUB_TOKEN', 'absent'))\n"
    )
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code)
    before = snapshot(pyeuvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    result = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "runtime-output")
    assert snapshot(pyeuvics) == before
    rendered = (
        result.staged_content / "software/notebooks/00_environment_check.md"
    ).read_text(encoding="utf-8")
    assert "../notebook-runtime-output/00_environment_check ok" in rendered
    assert "token=absent" in rendered
    assert "ghp_" not in rendered


@pytest.mark.parametrize(
    ("code", "options", "message"),
    [
        ("print('precomputed')\n", {"with_output": True}, "contains outputs"),
        ("raise RuntimeError('fixture failure')\n", {}, "execution failed"),
        ("import random\nprint(random.random())\n", {}, "nondeterministic"),
        (
            "from pathlib import Path\nprint(Path('secret.csv').read_text())\n",
            {"add_unapproved_data": True},
            "unapproved data dependency",
        ),
        ("print('oversized source')\n", {"max_source_bytes": 10}, "source size limit"),
        ("print('oversized render')\n", {"max_rendered_bytes": 10}, "rendered notebook exceeds"),
    ],
)
def test_notebook_publication_failure_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    code: str,
    options: dict,
    message: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code, **options)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-output")

"""Independent final-byte comparison across publication modes and EUVICS schemas."""

from __future__ import annotations

import copy
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.support.overview import write_overview_candidate
from tests.support.paths import ROOT
from tests.support.publication import (
    add_approved_campaign_set,
    add_approved_notebook_set,
    add_proposal_release,
    create_sources,
    euvics_manifest,
    pending_pyeuvics_set,
    pyeuvics_manifest,
    snapshot,
    write_locks,
)
from tools.review_manifest import compare_artifacts, read_review_manifest
from tools.site_assembly import assemble_site, pipeline
from tools.validate_ci import write_review_manifest

FIGURES = tuple(
    "docs/generated/overview-figures/kinetic-energy-scan." + suffix
    for suffix in ("svg", "csv", "json")
)


def commit_all(root: Path) -> str:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "Finalize independent acceptance fixture"],
        cwd=root,
        check=True,
    )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def make_matrix_sources(tmp_path: Path, schema: str, mode: str):
    eu = euvics_manifest()
    py = pyeuvics_manifest()
    if mode == "empty":
        eu["allowlist"] = []
        py["allowlist"] = []
    py["candidate_sets"] = [pending_pyeuvics_set()]
    e, p, commits = create_sources(tmp_path, euvics=eu, pyeuvics=py)
    if mode != "empty":
        (p / "docs/index.md").write_text(
            """# Generic package

[Inline](guide.md#generic-guide)
[Reference][guide]

[guide]: guide.md?view=public#generic-guide

<a href="guide.md#generic-guide">HTML guide</a>

`[Literal](unpublished.md)` is code, not a link.
""",
            encoding="utf-8",
        )
    if mode == "full":
        add_proposal_release(e)
        add_approved_notebook_set(p, "print('Repeatable synthetic output')\n")
        manifest_path = p / "publication/public-content-v1.json"
        notebooks = json.loads(manifest_path.read_text(encoding="utf-8"))[
            "candidate_sets"
        ]
        add_approved_campaign_set(p)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate_sets"].extend(notebooks)
        manifest["candidate_sets"].append(pending_pyeuvics_set())
        write_overview_candidate(p)
        figure = copy.deepcopy(manifest["candidate_sets"][0])
        figure.update(
            name="approved-figure-fixture",
            files=list(FIGURES),
            publication_status="approved-public-model-calculation",
            validation_status="calculated-unvalidated",
        )
        manifest["candidate_sets"].append(figure)
        manifest["package"]["version"] = "0.5.0"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    ep = e / "publication/public-content-v1.json"
    manifest = json.loads(ep.read_text(encoding="utf-8"))
    manifest["schema_version"] = schema
    if schema == "1.1":
        for entry in manifest["allowlist"]:
            entry["approval"]["sha256"] = hashlib.sha256(
                (e / entry["path"]).read_bytes()
            ).hexdigest()
    ep.write_text(json.dumps(manifest), encoding="utf-8")
    commits["euvics"] = commit_all(e)
    # Empty mode may otherwise have no changed package files.
    manifest_path = p / "publication/public-content-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    commits["pyeuvics"] = commit_all(p)
    return e, p, write_locks(tmp_path / "sources.lock.yml", commits)


def complete_bytes(root: Path) -> dict[str, bytes]:
    files = {}
    for path in root.rglob("*"):
        assert not path.is_symlink(), path
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    assert files
    return files


@pytest.mark.parametrize("schema", ["1.0", "1.1"])
@pytest.mark.parametrize("mode", ["empty", "partial", "full"])
def test_complete_artifact_repeatability_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, schema: str, mode: str
) -> None:
    e, p, lock = make_matrix_sources(tmp_path, schema, mode)
    before = (snapshot(e), snapshot(p))
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    timings = {}
    for name in (
        "_prepare_build",
        "_materialize_build",
        "_render_build",
        "_verify_build",
        "_finalize_build",
    ):
        original = getattr(pipeline, name)

        def measured(*args, _original=original, _name=name, **kwargs):
            started = time.perf_counter()
            try:
                return _original(*args, **kwargs)
            finally:
                timings.setdefault(_name, []).append(
                    round(time.perf_counter() - started, 4)
                )

        monkeypatch.setattr(pipeline, name, measured)
    first = assemble_site(ROOT, lock, e, p, tmp_path / "first")
    second = assemble_site(ROOT, lock, e, p, tmp_path / "second")
    a = complete_bytes(first.site)
    b = complete_bytes(second.site)
    assert a.keys() == b.keys()
    assert {name for name in a if a[name] != b[name]} == set()
    # No generated file, provenance field or timestamp is normalized away.
    for name in (
        "staged-content-inventory.json",
        "staging-plan.json",
        "artifact-plan.json",
        "publication-artifact-manifest.json",
    ):
        assert (first.output_root / name).read_bytes() == (
            second.output_root / name
        ).read_bytes(), name
    for name in (
        "notebook-execution-provenance.json",
        "source-build/document-build-evidence.json",
    ):
        x = first.output_root / name
        y = second.output_root / name
        assert x.exists() == y.exists()
        if x.exists():
            assert x.read_bytes() == y.read_bytes(), name
    assert (snapshot(e), snapshot(p)) == before
    assert not any("notes/note" in name for name in a)
    assert ("documents/proposal.pdf" in a) == (mode == "full")
    assert ("software/notebooks/00_environment_check/index.html" in a) == (
        mode == "full"
    )
    assert ("imported/pyeuvics/" + FIGURES[0] in a) == (mode == "full")
    if mode == "full":
        assert (
            a["documents/proposal.pdf"] == (e / "build/proposal/main.pdf").read_bytes()
        )
        for relative in FIGURES:
            assert a["imported/pyeuvics/" + relative] == (p / relative).read_bytes()
        assert b"Calculated" in a["project/overview/index.html"]
        assert (
            b"Repeatable synthetic output"
            in a["software/notebooks/00_environment_check/index.html"]
        )
    if mode != "empty":
        html = a["imported/pyeuvics/docs/index.html"].decode()
        assert (
            "guide/#generic-guide" in html
            and "guide/?view=public#generic-guide" in html
        )
        assert "[Literal](unpublished.md)" in html
    # Independently computed public bytes must agree with the proposal manifest,
    # not merely with another invocation of its own writer.
    manifest_path = write_review_manifest(first.output_root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public = {
        item["path"][5:]: item
        for item in manifest["files"]
        if item["path"].startswith("site/")
    }
    assert set(public) == set(a)
    for name, data in a.items():
        assert public[name]["sha256"] == hashlib.sha256(data).hexdigest()
        assert public[name]["bytes"] == len(data)
    other_path = write_review_manifest(second.output_root)
    assert manifest_path.read_bytes() == other_path.read_bytes()
    # A single controlled byte change must appear in comparison evidence.
    changed = second.site / "index.html"
    changed.write_bytes(changed.read_bytes() + b"\n<!-- synthetic change -->\n")
    write_review_manifest(second.output_root)
    comparison = compare_artifacts(
        read_review_manifest(manifest_path), read_review_manifest(other_path)
    )
    assert comparison.changed == ("site/index.html",)
    unit = 1 if sys.platform == "darwin" else 1024
    print(
        "MATRIX_METRICS "
        + json.dumps(
            {
                "schema": schema,
                "mode": mode,
                "public_files": len(a),
                "public_bytes": sum(map(len, a.values())),
                "phase_seconds": timings,
                "process_peak_rss_bytes": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss
                * unit,
                "children_peak_rss_bytes": resource.getrusage(
                    resource.RUSAGE_CHILDREN
                ).ru_maxrss
                * unit,
            },
            sort_keys=True,
        )
    )


def test_full_matrix_corrupt_pdf_never_promotes_and_preserves_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.site_assembly import AssemblyError

    e, p, lock = make_matrix_sources(tmp_path, "1.1", "full")
    before = (snapshot(e), snapshot(p))
    sentinel = tmp_path / "caller-owned.txt"
    sentinel.write_text("keep", encoding="utf-8")
    render = pipeline._render_build

    def corrupt(context, entries):
        result = render(context, entries)
        pdf = result.site / "documents/proposal.pdf"
        pdf.write_bytes(pdf.read_bytes() + b"\n% altered final artifact\n")
        return result

    monkeypatch.setattr(pipeline, "_render_build", corrupt)
    output = tmp_path / "failed"
    with pytest.raises(AssemblyError, match="checksum mismatch"):
        assemble_site(ROOT, lock, e, p, output, source_date_epoch="1785628800")
    assert not output.exists()
    retained = list(tmp_path.glob(".failed.assembly-*/INCOMPLETE.json"))
    assert len(retained) == 1
    assert json.loads(retained[0].read_text(encoding="utf-8")) == {
        "status": "incomplete",
        "phase": "verify",
        "error_type": "OwnershipError",
    }
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert (snapshot(e), snapshot(p)) == before

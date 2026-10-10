"""Discover, validate, describe, and safely propose exact source-lock updates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.review_manifest import (
    ReviewManifest,
    ReviewManifestError,
    compare_artifacts,
    read_review_manifest,
)
from tools.site_assembly.contracts import COMMIT_RE, ContractError, load_locks
from tools.site_assembly.presentation import Code, render_value
from tools.site_assembly.primitives import FileOperationError, atomic_write_text
from tools.validation_evidence import (
    EvidenceError,
    validate_pair,
    verify_bundle,
    write_ancestry,
    write_bundle,
)


class SourceUpdateError(ValueError):
    """A candidate source-lock proposal is unsafe or incomplete."""


def _checkout_head(source: Path, name: str) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=source, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.output.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        raise SourceUpdateError(f"cannot resolve authenticated {name} checkout HEAD: {detail}") from exc
    if COMMIT_RE.fullmatch(commit) is None:
        raise SourceUpdateError(f"authenticated {name} checkout HEAD is invalid")
    return commit


def discover(lock_path: Path, checkouts: dict[str, Path]) -> dict[str, str]:
    """Resolve authenticated source checkout HEADs to exact candidates."""

    locks = load_locks(lock_path)
    if set(checkouts) != {"euvics", "pyeuvics"}:
        raise SourceUpdateError("authenticated discovery requires both source checkouts")
    result = {name: _checkout_head(checkouts[name], name) for name in ("euvics", "pyeuvics")}
    result["has_updates"] = str(
        any(result[name] != locks[name].commit for name in ("euvics", "pyeuvics"))
    ).lower()
    return result


def apply_candidates(lock_path: Path, output_path: Path, candidates: dict[str, str]) -> None:
    """Write a candidate lock that differs only by validated commit values."""

    current = load_locks(lock_path)
    if set(candidates) != {"euvics", "pyeuvics"}:
        raise SourceUpdateError("candidate commits must contain exactly euvics and pyeuvics")
    for name, commit in candidates.items():
        if COMMIT_RE.fullmatch(commit) is None:
            raise SourceUpdateError(f"candidate commit is invalid for {name}")
    raw = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    for name in ("euvics", "pyeuvics"):
        raw["sources"][name]["commit"] = candidates[name]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    updated = load_locks(output_path)
    for name in ("euvics", "pyeuvics"):
        if (
            updated[name].repository != current[name].repository
            or updated[name].manifest_path != current[name].manifest_path
        ):
            raise SourceUpdateError(f"candidate lock changed immutable source fields for {name}")


def verify_lock_change(current_path: Path, candidate_path: Path) -> tuple[str, ...]:
    """Require a commit-only, nonempty change between two strict lock files."""

    current = load_locks(current_path)
    candidate = load_locks(candidate_path)
    changed: list[str] = []
    for name in ("euvics", "pyeuvics"):
        before, after = current[name], candidate[name]
        if before.repository != after.repository or before.manifest_path != after.manifest_path:
            raise SourceUpdateError(f"candidate lock changed immutable source fields for {name}")
        if before.commit != after.commit:
            changed.append(name)
    if not changed:
        raise SourceUpdateError("candidate source lock contains no commit update")
    return tuple(changed)


def verify_ancestry(
    current_path: Path,
    candidate_path: Path,
    checkouts: dict[str, Path],
    evidence_output: Path | None = None,
) -> None:
    """Reject rewinds or unrelated histories for default-branch candidates."""

    current = load_locks(current_path)
    candidate = load_locks(candidate_path)
    verify_lock_change(current_path, candidate_path)
    for name in ("euvics", "pyeuvics"):
        if current[name].commit == candidate[name].commit:
            continue
        try:
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", current[name].commit, candidate[name].commit],
                cwd=checkouts[name],
                check=False,
            )
        except OSError as exc:
            raise SourceUpdateError(f"cannot verify source ancestry for {name}: {exc}") from exc
        if result.returncode != 0:
            raise SourceUpdateError(f"candidate commit is not a descendant of the locked {name} commit")

    if evidence_output is not None:write_ancestry(evidence_output,current_path,candidate_path)


def _read_review_manifest(path: Path) -> ReviewManifest:
    try:
        return read_review_manifest(path)
    except ReviewManifestError as exc:
        raise SourceUpdateError(str(exc)) from exc


def write_comparison(
    current_lock_path: Path,
    candidate_lock_path: Path,
    baseline_manifest_path: Path,
    candidate_manifest_path: Path,
    output_path: Path,
    evidence_root: Path | None = None,
    website_root: Path | None = None,
) -> None:
    """Write a bounded PR body comparing complete validated artifacts."""

    current = load_locks(current_lock_path)
    candidate = load_locks(candidate_lock_path)
    changed_sources = verify_lock_change(current_lock_path, candidate_lock_path)
    baseline = _read_review_manifest(baseline_manifest_path)
    proposed = _read_review_manifest(candidate_manifest_path)
    if evidence_root is not None:
        if website_root is None or output_path.resolve()!=(evidence_root/'proposal/pull-request.md').resolve():raise SourceUpdateError('bound evidence requires the canonical proposal report and website')
        if baseline_manifest_path.resolve()!=(evidence_root/'baseline/review-artifact-manifest.json').resolve() or candidate_manifest_path.resolve()!=(evidence_root/'candidate/review-artifact-manifest.json').resolve():raise SourceUpdateError('comparison manifests differ from the evidence package')
        validate_pair(evidence_root,website_root,current_lock_path,candidate_lock_path)
    validation_statement=(
        'Bound records confirm both complete artifacts passed publication-contract validation, website tests, strict typing, strict MkDocs build, assembly, artifact validation and manifest hashing. Source ancestry checks are bound to these exact locks. '
        'This is workflow consistency evidence, not scientific approval or authentication against a compromised validator.\n\n'
        if evidence_root is not None else
        'Comparison only: validation and ancestry records were not supplied. This report does not attest that those checks passed.\n\n'
    )
    comparison=compare_artifacts(baseline,proposed)
    added,removed,changed=comparison.added,comparison.removed,comparison.changed
    comparison_path=output_path.with_name(output_path.name+'.json')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_text(comparison_path,json.dumps(comparison.to_dict(),indent=2,sort_keys=True)+'\n')

    def path_list(items: tuple[str,...]) -> str:
        shown='\n'.join('- '+render_value(Code(item)) for item in items[:100]) or '- None'
        if len(items)>100:
            shown+=f'\n\nShowing 100 of {len(items)} paths; {len(items)-100} omitted here. The machine-readable comparison retains every path.'
        return shown

    source_rows = "\n".join(
        f"| {name} | `{current[name].commit}` | `{candidate[name].commit}` | "
        f"{'Updated' if name in changed_sources else 'Unchanged'} |"
        for name in ("euvics", "pyeuvics")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "## Automated source-lock proposal\n\n"
        "This pull request proposes exact source commits only. It does not merge itself, deploy, "
        "change a publication manifest, or follow a branch tip in production.\n\n"
        "### Source provenance\n\n"
        "| Source | Current commit | Candidate commit | State |\n"
        "| --- | --- | --- | --- |\n"
        f"{source_rows}\n\n"
        f"{validation_statement}"
        "### Artifact comparison\n\n"
        f"- Added files: {len(added)}\n"
        f"- Removed files: {len(removed)}\n"
        f"- Changed files: {len(changed)}\n"
        f"- Baseline files: {comparison.baseline_files}\n"
        f"- Candidate files: {comparison.candidate_files}\n\n"
        "<details><summary>Added paths</summary>\n\n"
        f"{path_list(added)}\n\n</details>\n\n"
        "<details><summary>Removed paths</summary>\n\n"
        f"{path_list(removed)}\n\n</details>\n\n"
        "<details><summary>Changed paths</summary>\n\n"
        f"{path_list(changed)}\n\n</details>\n\n"
        "### Required human review\n\n"
        "- [ ] Confirm each source manifest approval and scientific limitation.\n"
        "- [ ] Inspect the uploaded baseline/candidate manifests and review artifact diff.\n"
        "- [ ] Verify document, notebook, campaign, license, attribution, and permission changes.\n"
        "- [ ] Confirm the pull request changes only `sources.lock.yml`.\n"
        "- [ ] Select **Approve workflows to run** if GitHub requests it for this bot-created PR; "
        "otherwise manually run `site-check.yml` on this proposal branch if no check appears.\n"
        "- [ ] Require normal validation checks; do not merge on automation authority alone.\n"
        "- [ ] After merge, verify the protected Pages deployment and retain rollback provenance.\n",
        encoding="utf-8",
    )

    if evidence_root is not None and website_root is not None:
        write_bundle(evidence_root,website_root,current_lock_path,candidate_lock_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover_parser = subparsers.add_parser("discover")
    discover_parser.add_argument("--lock", type=Path, default=Path("sources.lock.yml"))
    discover_parser.add_argument("--euvics-source", type=Path, required=True)
    discover_parser.add_argument("--pyeuvics-source", type=Path, required=True)
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--lock", type=Path, required=True)
    apply_parser.add_argument("--output", type=Path, required=True)
    apply_parser.add_argument("--euvics-commit", required=True)
    apply_parser.add_argument("--pyeuvics-commit", required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--current", type=Path, required=True)
    verify_parser.add_argument("--candidate", type=Path, required=True)
    ancestry_parser = subparsers.add_parser("verify-ancestry")
    ancestry_parser.add_argument("--current", type=Path, required=True)
    ancestry_parser.add_argument("--candidate", type=Path, required=True)
    ancestry_parser.add_argument("--euvics-source", type=Path, required=True)
    ancestry_parser.add_argument("--pyeuvics-source", type=Path, required=True)
    ancestry_parser.add_argument("--output", type=Path)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--current", type=Path, required=True)
    compare_parser.add_argument("--candidate", type=Path, required=True)
    compare_parser.add_argument("--baseline-manifest", type=Path, required=True)
    compare_parser.add_argument("--candidate-manifest", type=Path, required=True)
    compare_parser.add_argument("--output", type=Path, required=True)
    compare_parser.add_argument('--evidence-root',type=Path)
    compare_parser.add_argument('--website-root',type=Path,default=Path('.'))
    evidence_parser=subparsers.add_parser('verify-evidence')
    evidence_parser.add_argument('--root',type=Path,required=True)
    evidence_parser.add_argument('--website-root',type=Path,default=Path('.'))
    evidence_parser.add_argument('--current',type=Path,required=True)
    evidence_parser.add_argument('--candidate',type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            checkouts = {"euvics": args.euvics_source, "pyeuvics": args.pyeuvics_source}
            print("\n".join(f"{key}={value}" for key, value in discover(args.lock, checkouts).items()))
        elif args.command == "apply":
            apply_candidates(
                args.lock,
                args.output,
                {"euvics": args.euvics_commit, "pyeuvics": args.pyeuvics_commit},
            )
        elif args.command == "verify":
            print("changed_sources=" + ",".join(verify_lock_change(args.current, args.candidate)))
        elif args.command == "verify-ancestry":
            verify_ancestry(
                args.current,
                args.candidate,
                {"euvics": args.euvics_source, "pyeuvics": args.pyeuvics_source},
                args.output,
            )
        elif args.command=='verify-evidence':
            verify_lock_change(args.current,args.candidate)
            verify_bundle(args.root,args.website_root,args.current,args.candidate)
        else:
            write_comparison(
                args.current,
                args.candidate,
                args.baseline_manifest,
                args.candidate_manifest,
                args.output,
                args.evidence_root,
                args.website_root,
            )
    except (ContractError, SourceUpdateError, EvidenceError, ReviewManifestError, FileOperationError, OSError) as exc:
        print(f"source update error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

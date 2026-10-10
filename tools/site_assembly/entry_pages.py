"""Website entry pages assembled from the staging plan publication view."""
import os
from pathlib import Path
from .publication import PublicationSource
from .presentation import Link, markdown_text, render_link, render_limitations
from .template_slots import fill_slot

def _relative_markdown_link(source_path: str, destination: Path, imported_root: Path) -> str:
    target = imported_root / source_path
    return os.path.relpath(target, destination.parent).replace(os.sep, "/")


def stage_source_entry_pages(
    contracts: tuple[PublicationSource, ...],
    staged_content: Path,
    imported_root: Path,
    timestamp: str,
) -> None:
    """Make website-owned entry pages reflect the validated build contents."""

    euvics = next(contract for contract in contracts if contract.lock.name == "euvics")
    pyeuvics = next(contract for contract in contracts if contract.lock.name == "pyeuvics")
    approved_markdown = {
        item.path: item for item in pyeuvics.files if Path(item.path).suffix.lower() == ".md"
    }
    versions = sorted({item.version for item in pyeuvics.files})
    statuses = sorted({item.publication_status for item in pyeuvics.files})
    limitations = sorted(
        {limitation for item in pyeuvics.files for limitation in item.known_limitations}
    )

    home = staged_content / "index.md"
    package_index = "docs/index.md"
    package_link = (
        f"[{len(pyeuvics.files)} manifest-approved pyEUVICS files]"
        f"({_relative_markdown_link(pyeuvics.destination(package_index), home, staged_content)})"
        if package_index in approved_markdown
        else f"{len(pyeuvics.files)} manifest-approved pyEUVICS files"
    )
    fill_slot(home, "availability",
        "## Approved content in this assembled build\n\n"
        f"- **pyEUVICS:** {package_link} from commit `{pyeuvics.lock.commit}`.\n"
        f"- **EUVICS documents:** {len(euvics.files)} manifest-approved files from commit "
        f"`{euvics.lock.commit}`.\n"
        f"- **Build timestamp:** {timestamp}\n\n"
        "[Approved documents](documents/index.md) · [Approved campaigns](campaigns/index.md) · [Static notebooks](software/notebooks/index.md) · [Downloads](downloads/index.md)\n",
    )

    project_overview = staged_content / "project/overview.md"
    euvics_source_lines = []
    for item in sorted(euvics.files, key=lambda entry: entry.path):
        if item.kind == "pdf":
            continue
        target = os.path.relpath(
            staged_content / euvics.destination(item.path),
            project_overview.parent,
        ).replace(os.sep, "/")
        euvics_source_lines.append(
            "- " + render_link(Link(item.title, target))
            + f" — version {markdown_text(item.version)}; status {markdown_text(item.publication_status)}"
        )
    euvics_sources = "\n".join(euvics_source_lines) or (
        "- No project-overview sources are approved by the locked EUVICS manifest."
    )
    fill_slot(project_overview, "provenance",
        "## Assembled build provenance\n\n"
        "This section is generated from the validated source locks; it is not "
        "maintained as scientific prose.\n\n"
        f"- **EUVICS source:** [{euvics.lock.commit}]"
        f"({euvics.lock.repository}/tree/{euvics.lock.commit})\n"
        f"- **pyEUVICS source:** [{pyeuvics.lock.commit}]"
        f"({pyeuvics.lock.repository}/tree/{pyeuvics.lock.commit})\n"
        f"- **Build timestamp:** {timestamp}\n\n"
        "### Approved EUVICS source inputs\n\n"
        f"{euvics_sources}\n",
    )

    sections: tuple[tuple[str, str, tuple[str, ...]], ...] = (
        (
            "software/installation.md",
            "pyEUVICS installation",
            ("README.md", "docs/index.md", "docs/getting-started/"),
        ),
        ("software/science.md", "pyEUVICS science and conventions", ("docs/science/",)),
        ("software/api.md", "pyEUVICS API reference", ("docs/api/",)),
        ("software/tutorials.md", "pyEUVICS tutorials", ("docs/tutorials/",)),
        ("software/workflows.md", "pyEUVICS workflows", ("docs/workflows/",)),
        ("software/validation.md", "pyEUVICS validation", ("docs/validation/",)),
    )
    for destination_name, heading, prefixes in sections:
        destination = staged_content / destination_name
        selected = pyeuvics.markdown(prefixes)
        links = "\n".join(
            "- " + render_link(Link(item.title, _relative_markdown_link(pyeuvics.destination(item.path), destination, staged_content)))
            for item in selected
        ) or "No source documents in this section are approved by the locked manifest."
        limitations_text = (
            render_limitations(tuple(limitations))
            if limitations
            else "- No global limitation is recorded by the source contract."
        )
        destination.write_text(
            f"# {heading}\n\n"
            "This assembled entry page links only to documentation authorized by the "
            "locked pyEUVICS publication contract. Scientific and software corrections "
            "belong in the authoritative source repository.\n\n"
            "## Build provenance\n\n"
            f"- **Source commit:** `{pyeuvics.lock.commit}`\n"
            f"- **Package version:** {', '.join(markdown_text(value) for value in versions) if versions else 'No approved version'}\n"
            f"- **Publication status:** {', '.join(markdown_text(value) for value in statuses) if statuses else 'No approved status'}\n"
            f"- **Build timestamp:** {timestamp}\n\n"
            "## Approved documentation\n\n"
            f"{links}\n\n"
            "## Known limitations\n\n"
            f"{limitations_text}\n",
            encoding="utf-8",
        )

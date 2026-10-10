"""Present admitted campaign metadata without notebook execution."""
from __future__ import annotations
from pathlib import Path
from .models import SourceContract
from .notebook_policy import NotebookError
from .presentation import Code, Link, MetadataRow, render_link, render_table, render_limitations

def stage_campaign_overviews(contract: SourceContract, staged_content: Path, timestamp: str) -> None:
    """Replace campaign placeholders only when exact campaign files are approved."""

    campaigns = {
        "reference_6p7nm": ("6.7 nm reference campaign", Path("campaigns/6-7-nm.md")),
        "reference_13p5nm": ("13.5 nm reference campaign", Path("campaigns/13-5-nm.md")),
    }
    for campaign, (title, overview_relative) in campaigns.items():
        approved = tuple(
            item for item in contract.files if item.path.startswith(f"campaigns/{campaign}/")
        )
        if not approved:
            continue
        status = {item.publication_status for item in approved}
        validation = {item.validation_status for item in approved}
        limitations = sorted({value for item in approved for value in item.known_limitations})
        if len(status) != 1 or len(validation) != 1 or None in validation:
            raise NotebookError(f"inconsistent approved campaign metadata: {campaign}")
        links = "\n".join(
            "- " + render_link(Link(item.title, f"../imported/pyeuvics/{item.path}")) for item in approved
        )
        limitation_text = render_limitations(tuple(limitations))
        fields = render_table((
            MetadataRow("pyEUVICS version", approved[0].version),
            MetadataRow("Source commit", Code(contract.lock.commit)),
            MetadataRow("Publication status", next(iter(status))),
            MetadataRow("Scientific validation status", next(iter(validation)) or ""),
            MetadataRow("Website build timestamp", timestamp),
        ))
        (staged_content / overview_relative).write_text(
            f"""# {title}

{fields}

## Approved campaign material

{links}

## Known limitations

{limitation_text}
""",
            encoding="utf-8",
        )

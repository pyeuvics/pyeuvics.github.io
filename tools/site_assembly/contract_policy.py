"""Reviewed source identities, schemas, file types and initial publication subsets."""
import re

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


GLOB_CHARS = set("*?[]{}")


SUPPORTED_SUFFIXES = {
    "", ".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js",
    ".json", ".csv", ".yaml", ".yml", ".txt", ".cff", ".pdf", ".ipynb",
    ".tex", ".bib", ".py",
}


KIND_SUFFIXES = {
    "markdown": {".md"},
    "latex-source": {".tex"},
    "bibliography": {".bib"},
    "metadata": {"", ".json", ".csv", ".yaml", ".yml", ".cff"},
    "pdf": {".pdf"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".svg"},
    "data": {".csv", ".json", ".yaml", ".yml", ".txt"},
}


EUVICS_ROOT_FIELDS = {
    "$schema", "schema_version", "contract_id", "repository", "default_policy",
    "allowlist", "exclusions", "publication_decisions",
}


PYEUVICS_ROOT_FIELDS = {
    "$schema", "schema_version", "contract_id", "repository", "package",
    "default_policy", "unpublished_link_policy", "allowlist", "candidate_sets",
    "excluded_prefixes",
}


PYEUVICS_REPOSITORY_FIELDS = {
    "url", "website_repository_url", "website_url", "source_commit_policy",
}


EUVICS_ENTRY_FIELDS = {
    "path", "kind", "title", "version", "publication_status", "approval",
    "license", "attribution", "known_limitations", "document_date",
}


PYEUVICS_SET_BASE_FIELDS = {
    "name", "status", "owner", "reason", "files", "dependencies",
    "max_bytes_per_notebook", "output_policy", "execution_policy", "random_seed",
    "configurations", "max_rendered_bytes",
}


PYEUVICS_SET_APPROVAL_FIELDS = PYEUVICS_SET_BASE_FIELDS | {
    "approval", "publication_status", "validation_status", "known_limitations",
    "local_requirements", "execution_policy", "random_seed", "configurations",
    "max_rendered_bytes",
}


PYEUVICS_SET_APPROVAL_REQUIRED = {
    "name", "status", "owner", "reason", "files", "dependencies", "approval",
    "publication_status", "validation_status", "known_limitations", "local_requirements",
}


INITIAL_NOTEBOOK_PATHS = {
    "notebooks/00_environment_check.ipynb",
    "notebooks/01_linear_ics_kinematics.ipynb",
    "notebooks/02_nonlinear_ics_and_harmonics.ipynb",
    "notebooks/03_parameter_scans.ipynb",
    "notebooks/04_end_to_end_digital_twin.ipynb",
    "notebooks/05_validation_and_cain_comparison.ipynb",
    "notebooks/12_reference_campaign_6p7nm.ipynb",
    "notebooks/13_reference_campaign_13p5nm.ipynb",
}


INITIAL_CAMPAIGN_PATHS = {
    f"campaigns/reference_{wavelength}/{relative}"
    for wavelength in ("6p7nm", "13p5nm")
    for relative in (
        "README.md",
        "figures/spectrum.svg",
        "reports/scientific_report.md",
        "reports/validation.md",
    )
}


INITIAL_OVERVIEW_FIGURE_PATHS = {
    "docs/generated/overview-figures/kinetic-energy-scan.svg",
    "docs/generated/overview-figures/kinetic-energy-scan.csv",
    "docs/generated/overview-figures/kinetic-energy-scan.json",
}

# Dependency and toolchain policy

`requirements-validation.txt` is the complete Python declaration for source-only
quality checks and source-backed validation. Both modes test real synthetic
notebooks and PDFs; only source-backed builds read approved source checkouts and
conditionally need external TeX tools. Install it in a fresh Python 3.13 virtual
environment, then run `python -m tools.dependencies` and `python -m tools.quality`.

Direct dependency roles are recorded in `tools/dependency-policy.json`:

- Site runtime: MkDocs, Markdown, YAML and bounded asset/parser libraries.
- Notebook runtime: nbclient/nbconvert/nbformat and the owned-kernel interfaces.
- Test tools: pytest, strict typing/stubs and ReportLab for synthetic PDF fixtures.
- Numerical notebooks: NumPy 2.5.3 and SciPy 1.18.1, reviewed for the shared
  Python 3.13 environment on 2026-10-11; other notebook pins are unchanged.
- External document tools: Make, latexmk, TeX and fonts, installed only when
  document candidates require them. These are separate from Python dependencies.

The proposal writer installs `requirements-docs.txt` with
`constraints-validation.txt`; core PyYAML is declared there directly. It does not
need numerical notebook packages or private source execution. The direct import
check and strict typing catch missing libraries and stubs.

Constraints preserve the installed versions reviewed on 2026-10-10, with the
numerical patch upgrades and types-PyYAML 6.0.12.20260906 reviewed on 2026-10-11.
They restrict
resolution of both direct and transitive packages without forcing inactive
platform dependencies to install. They are scoped to the Python 3.13 macOS/Linux
validation workflow, not a universal platform lock or an OS image. pip bootstrap
is observed in environment evidence rather than upgraded by this refactor.
Cached installation is an optimization; a fresh installation plus `pip check`,
dependency-policy checks and quality checks is the reproducibility test.

Validation records hash installed distribution files, the interpreter, package
versions and all dependency declarations. Notebook records also check installed
constraints and the locked source's numerical policy. The pending real source
policy requires NumPy 2.5.2 while the website now uses 2.5.3: that pending content
stays excluded; this work does not recalculate or approve it.

Document evidence records available Make/latexmk/pdfTeX/kpathsea/fontconfig version
reports and installed TeX/font package versions where the package manager exposes
them, plus executable/report fingerprints. Missing probes are explicit. This is
not a hermetic font/OS snapshot; exact rebuilt PDF byte equality with the approved
source artifact remains mandatory. A toolchain change must be reviewed rather
than accepting a new PDF hash automatically.

Dependency upgrades and advisory audits are separate reviewed work. Constraints
neither guarantee permanent registry availability nor establish permanent security.
Never auto-update numerical pins, source locks or approval hashes to satisfy an
advisory or resolver. Record fresh-install evidence and the tested platforms.

WEB-35 adds only Ruff 0.17.0 as a reviewed development tool. Numerical pins are unchanged.

Validation evidence records every dependency input and its SHA-256 digest in
canonical filename order, independently of dependency catalog order. Readers
reject unordered or duplicate entries; all policy and configuration inputs
remain bound to the validation record.

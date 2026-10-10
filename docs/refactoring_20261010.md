# Website refactoring backlog — 2026-10-10

## Review scope and status

- Repository: `pyeuvics/pyeuvics.github.io`.
- Reviewed HEAD: `b62dc0ace6898a6f1db3436fe397c51ecc204880`.
- Status: **review only; 36 queued tasks; no refactoring implemented**.
- Storage: this report and its execution record are intentionally untracked.
  Do not stage, commit, publish, or import them into website content.
- Coverage: inventory of all 105 tracked paths; detailed review of all 13
  Python tooling modules, all 10 test modules, all three workflows, MkDocs
  configuration, requirements, frontend assets/templates, website pages,
  current operating guidance, and relevant prior remediation records.
  Historical plans were used as context, not treated as current instructions.
- This is a comprehensive snapshot-based review, not a guarantee that every
  possible defect or future refactoring opportunity has been discovered.

The website is an independent publication consumer. Do not move scientific
calculations here, copy private upstream content into fixtures, or synchronize
validator implementations mechanically across repositories. Keep source
approval, website validation, and deployment authorization separate.

## Verified baseline

Checks ran in a disposable local clone using the existing documentation
environment, Python 3.13.16, on macOS. No dependency upgrade was performed.

| Check | Result |
| --- | --- |
| Existing suite, `python -m pytest -p no:cacheprovider` | 130 passed, 95.87 seconds |
| `python -m mypy --strict tools`, disposable cache | Passed, 13 source files |
| Standalone `python -m mkdocs build --strict`, disposable output | Passed |
| Existing environment, `python -m pip check` | No broken requirements |
| Focused synthetic edge-case probes | Findings E01–E09 below |

The suite includes synthetic full assemblies, PDF fixtures, and notebook
execution. This review did **not** fetch private sources, run assembly against
the real production locks, execute GitHub workflows, inspect secrets or live
repository settings, perform a fresh dependency installation, browse the live
site, or certify browser accessibility. Passing the baseline does not close
the uncovered cases below or establish hosted-CI/deployment readiness.

## Findings reproduced beyond the existing suite

All inputs in these probes were synthetic. No private data was used or exposed.

| Evidence | Observed behavior | Relevant tasks |
| --- | --- | --- |
| E01 | A pyEUVICS manifest allowlisted `ignored.md`; the file existed only as ignored, untracked content. Git status remained clean and `load_contract` accepted it under the locked commit. | WEB-04 |
| E02 | With an approved target relocated to another staging directory, reference-style Markdown and raw HTML links passed validation but retained their old destination. An inline-code example was rewritten when the same target also appeared as a real link. | WEB-10 |
| E03 | Rendered-link validation accepted a `base` element, a `data:text/html` anchor, and an inline CSS escaped `url` token referencing an absent file. These are parser/policy gaps, not evidence of an exploited production site. | WEB-11 |
| E04 | A numeric review-manifest digest raised uncaught `TypeError`; a parent-relative path with boolean byte size was accepted. The reader currently compares metadata rather than opening these paths, so this is not a demonstrated filesystem escape. | WEB-24 |
| E05 | An overview CSV containing `nan` in an interior wavelength value passed `_validate_set`. Monotonic comparisons alone do not establish finite valid values. | WEB-21 |
| E06 | `_scan_artifact` accepted an unexpected `.md` file and an SVG containing a synthetic script element. Its current checks cover extension and text privacy patterns, not complete ownership or active-content validation. | WEB-15, WEB-16 |
| E07 | `schema_version: true` was accepted by the source-lock loader because boolean equality matched integer `1`. | WEB-05 |
| E08 | Source inspection confirms validator extension names match MkDocs, but extension options do not: MkDocs uses arithmatex `generic: true`; the validator supplies names only. The existing parity test compares names only. | WEB-09 |
| E09 | `content/stylesheets/readthedocs.css` is a symlink to the canonical file in `docs/stylesheets/`, not a second independent stylesheet. `extra.css` is tracked but is not registered by MkDocs or referenced by active code. | WEB-30 |

## Priority, task type, and execution rules

- **P1:** close a confirmed correctness/publication-boundary gap, or establish
  a necessary safety boundary before broad restructuring.
- **P2:** reduce structural duplication, improve maintainability, and make
  verification more reliable.
- **P3:** bounded cleanup or optimization after higher-value changes.
- **R:** predominantly behavior-preserving refactor.
- **H:** correctness/hardening change; write a failing regression first and
  explicitly review any intentional behavior change.
- **V:** verification/infrastructure improvement.
- **D:** documentation/governance cleanup.

Implement in the numbered order below, unless a smaller urgent fix is isolated
with its own regression. The dependency column names prerequisites within this
backlog; task numbers are stable identifiers, not elapsed-time estimates.
Keep one coherent task per change. Do not use a refactoring task to upgrade
dependencies, expand approvals, update production locks, alter credentials,
rename required checks, weaken validation, or deploy implicitly.

For implementation, create the repository-required active execution plan,
record before/after evidence, run focused tests and the full baseline, then
archive the completed plan. Staging/committing/pushing requires the authority
applicable to that later request; this review grants none.

## Sequential checklist

| Order | Task | Priority/type | Dependencies |
| --- | --- | --- | --- |
| 01 | WEB-01 — Extract synthetic fixture builders | P2 R | — |
| 02 | WEB-02 — Separate unit, integration, and rendering tests | P2 R/V | 01 |
| 03 | WEB-03 — Consolidate small filesystem/process primitives | P2 R | 01–02 |
| 04 | WEB-04 — Bind every consumed source file to the locked Git tree | P1 H | 01, 03 |
| 05 | WEB-05 — Strict structured-input parsing and scalar validation | P1 H | 01, 03 |
| 06 | WEB-06 — Split contract adapters into typed validation stages | P2 R | 04–05 |
| 07 | WEB-07 — Add independent publication-contract conformance cases | P2 V | 06 |
| 08 | WEB-08 — Unify context-aware privacy scanning | P1 H/R | 03 |
| 09 | WEB-09 — Share exact Markdown rendering configuration | P1 H | 02 |
| 10 | WEB-10 — Rewrite links with syntax-aware destination mapping | P1 H/R | 09 |
| 11 | WEB-11 — Make active-content and resource-URL policy explicit | P1 H | 08–10 |
| 12 | WEB-12 — Escape metadata through typed page-rendering helpers | P2 H/R | 05, 09, 11 |
| 13 | WEB-13 — Introduce a typed staging plan and destination registry | P2 R | 06, 10, 12 |
| 14 | WEB-14 — Separate assembly phases and isolate partial outputs | P2 R/H | 03, 13 |
| 15 | WEB-15 — Verify complete staged and final artifact ownership | P1 H | 13–14 |
| 16 | WEB-16 — Validate imported assets by format and trust origin | P1 H | 08, 11, 15 |
| 17 | WEB-17 — Isolate document build/preflight and evidence handling | P2 R/H | 03, 05–06, 14, 16 |
| 18 | WEB-18 — Separate notebook admission, execution, and rendering | P2 R/H | 06, 08, 11–14 |
| 19 | WEB-19 — Make notebook kernel/environment provenance explicit | P2 H/V | 18 |
| 20 | WEB-20 — Bound notebook execution and document its trust model | P1 H/V | 18–19 |
| 21 | WEB-21 — Validate overview artifacts with typed finite data | P1 H | 05–06, 12, 16 |
| 22 | WEB-22 — Generate entry pages and downloads from one publication view | P2 R/H | 12–13, 17–18, 21 |
| 23 | WEB-23 — Route edit/provenance links by page ownership | P2 H/R | 13, 22 |
| 24 | WEB-24 — Type and validate review manifests before comparison | P1 H/R | 03, 05, 15 |
| 25 | WEB-25 — Extract source-update proposal lifecycle logic | P2 R/V | 02, 24 |
| 26 | WEB-26 — Bind proposal evidence to validated inputs | P2 H/V | 24–25 |
| 27 | WEB-27 — Share secret-free local/CI quality checks | P2 R/V | 02, 14 |
| 28 | WEB-28 — Deduplicate workflow setup without merging trust zones | P2 R/V | 25–27 |
| 29 | WEB-29 — Clarify dependency and toolchain reproducibility | P2 V/D | 19, 27–28 |
| 30 | WEB-30 — Simplify stylesheet ownership and layout layers | P3 R | 02 |
| 31 | WEB-31 — Make browser initialization and MathJax loading robust | P2 R/H | 09, 30 |
| 32 | WEB-32 — Replace frontend string assertions with behavior tests | P2 V | 22–23, 30–31 |
| 33 | WEB-33 — Reconcile current operating instructions with workflows | P2 D | 27–29 |
| 34 | WEB-34 — Separate current backlog from historical governance | P3 D | 33 |
| 35 | WEB-35 — Establish bounded lint, typing, and local-file hygiene | P3 R/V | 01–02, 27 |
| 36 | WEB-36 — Final independent end-to-end and performance acceptance | P2 V | All preceding applicable tasks |

## Task details

### WEB-01 — Extract synthetic fixture builders

- [ ] **Evidence:** `tests/test_source_assembly.py:116–501` mixes manifest,
  Git repository, document, notebook, campaign, snapshot, and assembly helpers
  into a 1,136-line test module. `tests/test_source_update.py:27` builds its
  own locks and repositories; overview tests build another contract variant.
- **Change:** move small, typed builders into a test-support package with
  explicit knobs for invalid cases. Separate immutable fixture descriptions
  from operations that commit synthetic repositories. Do not introduce a
  giant generic fixture framework or reuse production parsers to manufacture
  expected values.
- **Accept:** preserve all 130 collected baseline cases and meaningful failure
  messages; fixture repositories remain synthetic, isolated, and independent
  of developer Git identity/global settings. New helpers support E01–E07.
- **Risk:** accidentally weakening rejection cases while reorganizing tests.

### WEB-02 — Separate unit, integration, and rendering tests

- [ ] **Evidence:** many negative-input tests call full `assemble_site`;
  `tests/test_readthedocs_style.py:17` builds a site in a module-local fixture;
  source assembly tests combine multiple responsibilities and real kernels.
- **Change:** group tests by contracts, links, staging, documents, notebooks,
  workflows, and presentation. Run parser/path failures directly at the
  boundary being tested; retain representative end-to-end failures and real
  render/build coverage. Share immutable scaffold builds where appropriate.
- **Accept:** document test tiers and keep the full suite as the default;
  collect the same baseline coverage before moving assertions. No optional
  marker may silently remove security, PDF, or notebook checks from required CI.
- **Risk:** optimizing runtime by replacing the only integration evidence.

### WEB-03 — Consolidate small filesystem/process primitives

- [ ] **Evidence:** duplicate archive exporters in `documents.py:42` and
  `notebooks.py:43`; four hashing implementations in those modules,
  `pipeline.py:163`, and `validate_ci.py:56`; inconsistent subprocess error
  handling and full-memory archive/hash reads.
- **Change:** introduce focused helpers for streaming hashes, locked archive
  export, atomic small-file writes, and bounded subprocess diagnostics.
  Preserve caller-specific error context and sorted deterministic serialization.
  Use POSIX archive-path semantics everywhere, retaining symlink/member checks.
- **Accept:** tests cover invalid members, missing tools, failed commands,
  unreadable files, and stable hashes; callers do not expose credential values.
- **Risk:** over-generalizing unlike document and notebook policies. Share
  mechanisms, not their admission or execution policies.

### WEB-04 — Bind every consumed source file to the locked Git tree

- [ ] **Evidence:** E01; `contracts.py:172` verifies only the manifest is
  tracked. `_validate_file` at line 198 checks live filesystem presence and
  symlinks, not Git-tree membership. Git status does not report ignored files.
- **Change:** resolve all admitted files, notebook dependencies/configurations,
  and citation inputs against the exact locked tree. Read from a verified
  immutable export, or check tracked object membership and bytes before use.
  Reject ignored, untracked additions even when a manifest names them.
- **Accept:** E01 fails closed; tracked ordinary files and approved tracked
  PDF baselines still work; dirty tracked files, symlink ancestors, mismatched
  commits, and unavailable objects remain rejected. Repeat checks at meaningful
  execution boundaries without claiming complete protection from concurrent
  hostile mutation of a developer machine.
- **Risk:** changing legitimate generated-file expectations; retain the explicit
  tracked-release/rebuild distinction for approved PDFs.

### WEB-05 — Strict structured-input parsing and scalar validation

- [ ] **Evidence:** E07; `contracts.py:119–161` uses dictionary checks plus
  equality for schema values, and `_load_json:188` uses default JSON decoding.
  Approval dates are validated differently between source adapters;
  `documents.py:97` only checks document-date shape.
- **Change:** add duplicate-key-rejecting JSON/YAML readers and precise
  validators for mappings with string keys, integer-but-not-boolean fields,
  nonblank text, actual ISO calendar dates, digests, and finite numbers where
  applicable. Convert malformed inputs into labelled domain errors.
- **Accept:** cover duplicate fields, booleans, mixed-type keys, impossible
  dates, wrong scalar/container types, decoding failures, and unknown fields.
  Preserve supported EUVICS 1.0/1.1 and pyEUVICS 1.0 contracts explicitly.
- **Risk:** narrowing accepted input is a deliberate hardening change, not
  a supposedly behavior-neutral helper extraction.

### WEB-06 — Split contract adapters into typed validation stages

- [ ] **Evidence:** `contracts.py:211–603` combines two source adapters,
  schema dispatch, exclusions, approvals, candidate states, notebook execution
  settings, static-set completeness, and dataclass construction.
- **Change:** retain a small `load_contract` facade; separate lock decoding,
  EUVICS versions, pyEUVICS package metadata, and candidate-set variants.
  Parse untyped JSON once into validated records. Centralize reviewed subset
  definitions without turning them into unrestricted globs or auto-discovery.
- **Accept:** equivalence tests retain sort order, provenance, rejection
  behavior, and source identities; adding a contract version requires an
  explicit adapter and reviewed fixtures. Avoid `str()` coercion as validation.
- **Risk:** silently admitting a pending set or expanding the reviewed subset.

### WEB-07 — Add independent publication-contract conformance cases

- [ ] **Evidence:** prior plan `029_publication-contract-consumer-alignment.md`
  documents consumer drift; current compatibility cases in
  `tests/test_source_assembly.py:754` cover a limited hand-built matrix.
- **Change:** add versioned, neutral valid/invalid contract vectors and
  expected outcomes for each supported producer version. Include approval
  states, exact-file rules, candidate dependencies, structured values, and
  content-policy cases. Keep the website's implementation independent.
- **Accept:** CI exercises all vectors without importing upstream code,
  requiring private sources, or changing production locks. If a shared corpus
  is later adopted by the source repos, coordinate it as separately authorized
  work with explicit version compatibility, not copied validator code.
- **Risk:** fixtures becoming self-confirming snapshots rather than independent
  statements of the publication contract.

### WEB-08 — Unify context-aware privacy scanning

- [ ] **Evidence:** `pipeline.py:30–62,182`, `notebooks.py:20–37,69`,
  `verify_runner_credentials.py:15–37`, and several tests use different path
  and credential patterns; notebook checks lack the same JWT/path coverage.
- **Change:** provide one reviewed pattern vocabulary with separate profiles
  for source text, notebook output, generated public text, and runner residue.
  Use bounded/streaming reads for large files and safe diagnostics naming the
  file and rule, never the matched secret. Do not treat a regex scan as proof
  that no credentials or private information can exist.
- **Accept:** shared synthetic corpus covers token forms, Windows escaping,
  POSIX paths, harmless URLs/drive descriptions, unreadable files, and marker
  boundaries across streamed blocks. Retain the runner's fail-closed behavior.
- **Risk:** broad false positives or weaker scans after naive deduplication.

### WEB-09 — Share exact Markdown rendering configuration

- [ ] **Evidence:** E08; `pipeline.py:65,232` provides extension names only;
  `mkdocs.yml:41–48` configures arithmatex options; the test at
  `tests/test_source_assembly.py:107` compares names, not options/output.
- **Change:** derive the publication validator's renderer from an explicitly
  validated website renderer configuration, including extension settings and
  order. Avoid maintaining a second approximation of the MkDocs parser.
- **Accept:** compare rendered behavior for math, attributes, nested Markdown,
  HTML, code, and tables under exactly the site settings. Configuration changes
  fail compatibility checks until intentionally reviewed; inert math support
  must remain, with executable script rejection intact.
- **Risk:** renderer changes silently altering security checks or equations.

### WEB-10 — Rewrite links with syntax-aware destination mapping

- [ ] **Evidence:** E02; `pipeline.py:261` validates rendered targets but
  `LINK_RE` rewrites only inline-link-shaped source substrings. Target-string
  membership does not distinguish an actual link from a code example.
- **Change:** use one syntax-aware representation for link validation and
  transformation. Support inline/reference links, raw HTML/resource attributes,
  images, approved PDF/notebook relocations, fragments, queries, and percent
  encoding without editing code examples. Define unsupported forms explicitly.
- **Accept:** relocated approved targets work in all supported forms; the same
  URL in inline/fenced code remains byte-identical; unpublished/escaping targets
  still fail. Verify emitted URLs and fragments in the built site, not only
  transformed Markdown substrings.
- **Risk:** broad Markdown serialization changes; bound them with golden cases.

### WEB-11 — Make active-content and resource-URL policy explicit

- [ ] **Evidence:** E03; `pipeline.py:81–160,195` uses HTML parsing plus
  CSS regexes and a context-free scheme allowlist. The current policy permits
  `data` for every URL-bearing context and does not reject `base`.
- **Change:** distinguish navigation URLs, image data, styles, and executable
  contexts. Define allowed elements/attributes and reject base-URL mutation,
  dangerous encoded schemes, unsupported CSS/resource syntax, and executable
  payloads. Use a proper CSS parser or deliberately reject unsupported CSS
  rather than expanding a collection of regex approximations.
- **Accept:** add benign and hostile fixtures for escaping, CSS comments and
  escapes, base/meta elements, srcset, embedded data, styles, and SVG references.
  Preserve legitimate math data islands and approved images. Any new parser
  dependency requires a documented, reviewed need.
- **Risk:** over-rejecting scientific markup or pretending approval alone makes
  arbitrary browser-active content safe.

### WEB-12 — Escape metadata through typed page-rendering helpers

- [ ] **Evidence:** `pipeline.py:291,411`, `documents.py:105`,
  `notebooks.py:205,308`, and `overview_figures.py:86` interpolate titles,
  limitations, versions, and status strings into Markdown/HTML.
- **Change:** introduce presentation view models and small renderers with
  explicit plain-text, Markdown, URL, table-cell, and attribute escaping.
  Share provenance/limitations rendering while retaining source-specific
  fields and exact scientific qualifications. Do not use a global text escape
  that corrupts equations or already-reviewed source Markdown.
- **Accept:** pipes, brackets, quotes, newlines, HTML-looking metadata, Unicode,
  and long fields cannot inject markup or break tables. Snapshot existing
  ordinary pages; confirm licenses/attribution remain visible for notebooks as
  well as documents.
- **Risk:** cosmetic normalization changing a scientific limitation's meaning.

### WEB-13 — Introduce a typed staging plan and destination registry

- [ ] **Evidence:** `models.py:58–87` models admitted source items and final
  entries, but mapping is assembled separately in `pipeline.py:317`,
  `documents.py:146`, and `notebooks.py:240`; website-generated pages are
  implicit side effects.
- **Change:** precompute a plan describing source identity, exact input bytes,
  output path, producer, page ownership, and generated relationships. Validate
  duplicate destinations, file/directory conflicts, and portable case aliases
  before writing; distinguish website assets, imports, rendered pages, and
  generated provenance.
- **Accept:** deterministic plans for zero/one/multiple publication sets;
  collisions fail before work; every planned output has one owner. Preserve
  public routes, existing inventory compatibility, and explicit approval rules.
- **Risk:** replacing a simple pipeline with an unnecessary plugin framework.

### WEB-14 — Separate assembly phases and isolate partial outputs

- [ ] **Evidence:** `pipeline.py:562` orchestrates all stages directly and
  writes the requested output before later steps can fail; `validate_ci.py:32`
  mutates process-wide timestamp state; output existence then prevents retry.
- **Change:** create a small build context with paths, validated timestamp,
  contracts, and stage results. Separate plan, materialize, render, verify,
  and finalize. Build in a uniquely owned workspace and promote only verified
  output; preserve a labelled failure workspace when useful for diagnostics.
- **Accept:** injected failures at each stage cannot be mistaken for complete
  output; retries are safe; existing outputs are never overwritten or broadly
  deleted. Timestamp validation agrees across direct and CI entry points.
- **Risk:** cleanup deleting user directories or atomicity claims unsupported
  across different filesystems.

### WEB-15 — Verify complete staged and final artifact ownership

- [ ] **Evidence:** E06; `_copy_contract` checks one imported subtree,
  `_write_inventory` records imported/generated source entries, and
  `_scan_artifact:546` accepts any file with an allowed suffix. Website
  `content` is copied recursively, including files not tied to a tracked index.
- **Change:** reconcile website-owned tracked inputs, generated pages,
  imported assets, MkDocs/theme outputs, and downloadable artifacts against a
  complete expected output graph. Check missing/extra paths, symlinks, ownership,
  and checksums. Explicitly allow the repository's internal canonical CSS
  symlink; reject unrelated/external aliases.
- **Accept:** extra ordinary `.md`/asset files and missing expected files fail;
  inventories account for intended theme assets without a blanket wildcard;
  final manifests cannot merely certify whatever happened to be produced.
- **Risk:** accidentally treating trusted theme output and imported source
  content as the same security category.

### WEB-16 — Validate imported assets by format and trust origin

- [ ] **Evidence:** E06; `_copy_contract` only text-scans non-Markdown assets;
  artifact scans do not inspect PDF contents, compressed/map payloads, or SVG
  active structure. `documents.py:77` checks PDF readability, not the complete
  public-content policy. The schematic has stronger source-specific tests.
- **Change:** use format-specific validators for imported SVG, PDF, CSS,
  JSON/maps, and permitted compressed outputs. Bound decoding/decompression;
  inspect relevant text/metadata and active/external references. Treat trusted
  Material JavaScript separately from imported browser-active content.
- **Accept:** synthetic embedded active content, unsafe references, malformed
  formats, oversized/decompression cases, and hidden-path fixtures fail with
  safe messages; normal approved assets retain bytes/checksums. Explain what
  raster-image/manual privacy review still cannot be automated.
- **Risk:** claiming that structural validation certifies copyright, scientific
  approval, or complete absence of sensitive information.

### WEB-17 — Isolate document build/preflight and evidence handling

- [ ] **Evidence:** `documents.py:146` combines export, build commands, log
  inspection, hash comparison, PDF validation, page rendering, and copying.
  `ci_source_locks.py:38` reports `approved_pdf` from a raw `kind == pdf`
  presence check before full metadata validation.
- **Change:** separate validated toolchain requirements, disposable document
  build, verification, and publication rendering. Make preflight terminology
  accurately distinguish a PDF candidate from a validated release. Collect
  bounded build evidence through a typed result and preserve byte-identity
  approval rather than relaxing reproducibility to fit a different toolchain.
- **Accept:** test zero PDFs, Proposal only, CDR only, both, bad dates, broken
  logs, missing output, build failure, and hash mismatch. Keep source trees
  untouched and reject all unapproved document artifacts.
- **Risk:** website code taking ownership of upstream document-release policy.

### WEB-18 — Separate notebook admission, execution, and rendering

- [ ] **Evidence:** `notebooks.py:76–202` mixes parsing, source scans, data
  inference, environment setup, execution, mutation checks, MIME handling,
  export, and size checks. Campaign-page rendering is in the same module.
- **Change:** define validated notebook inputs and an execution/render result;
  isolate each phase behind a small interface. Move campaign pages to the
  presentation layer. Route rendered Markdown through the same content policy
  as other imported material, with notebook-specific MIME/resource constraints.
  Normalize presentation headings without rewriting scientific cell content.
- **Accept:** preserve dual execution and source immutability; check one page
  H1, asset ownership, unsupported MIME, malformed resources, and source/output
  bounds. Mock execution only in unit tests; retain real-kernel integration.
- **Risk:** treating nbconvert output as trusted without applying publication
  rules, or reducing nondeterminism checks during a module split.

### WEB-19 — Make notebook kernel/environment provenance explicit

- [ ] **Evidence:** `notebooks.py:122` requests generic `kernel_name="python3"`
  and inherits selected host variables; metadata advertises `random_seed`
  while execution only sets `PYTHONHASHSEED`. Scientific RNG use is left to
  notebook code, and no resolved kernel identity is recorded.
- **Change:** resolve a kernel backed by the intended interpreter, isolate its
  spec/runtime caches, and record interpreter/package/source fingerprints.
  Define seed metadata precisely: Python hash randomization is not NumPy or
  Python RNG seeding. Do not silently prepend scientific seed code to reviewed
  notebooks. Validate numerical requirements against the locked source policy.
- **Accept:** a hostile or unrelated globally registered `python3` kernel
  cannot be selected accidentally; environment mismatch is explicit; deterministic
  fixtures pass twice and intentionally random fixtures still fail.
- **Risk:** changing scientific outputs or source approvals under an environment
  refactor. Such changes need separate source review.

### WEB-20 — Bound notebook execution and document its trust model

- [ ] **Evidence:** `notebooks.py:27,94` uses code/data regexes;
  `_archive_checkout` exports the entire locked repository; a temporary HOME
  and environment filter are not filesystem/network isolation. Per-cell
  timeout and post-render limits do not bound all execution/resource behavior.
- **Change:** explicitly document trusted-source execution and its limits;
  add total-time/output/resource budgets, robust cancellation/kernel cleanup,
  and isolated per-run writable directories. Evaluate OS/container isolation
  only through a separately approved design if untrusted execution is required.
  Do not claim regexes enforce an execution sandbox or complete data access.
- **Accept:** synthetic timeout, partial failure, residual process, excessive
  output, undeclared access, and cancellation tests; fail closed where a policy
  cannot be enforced. Preserve read-only/write-job separation and credential
  scrubbing; never request broader credentials for this work.
- **Risk:** new sandbox/network controls or platform dependencies are scope
  changes, not automatic refactoring authority.

### WEB-21 — Validate overview artifacts with typed finite data

- [ ] **Evidence:** E05; `overview_figures.py:27` assumes dictionary-shaped
  JSON, partially validates package metadata, parses float columns without
  finiteness/positivity checks, and validates trends using comparisons that
  admit NaN. Only a few acceptance cases exist in `test_overview_figures.py`.
- **Change:** parse a typed figure descriptor and data table; validate headers,
  counts, finite/physical values, reviewed grid, package version, settings,
  accessible SVG identifiers, and artifact consistency. Wrap JSON/XML/CSV
  errors in `OverviewFigureError`. Keep the approved model specification
  data-driven; never reimplement the physics to verify a plot.
- **Accept:** NaN/infinity, missing version, invalid root types, malformed SVG,
  inconsistent metadata and data, incomplete sets, and bad accessibility labels
  fail; the existing reviewed figure set remains accepted.
- **Risk:** scientific correctness must remain upstream; structural checks do
  not independently validate the model or provenance claim.

### WEB-22 — Generate entry pages and downloads from one publication view

- [ ] **Evidence:** `pipeline.py:411` appends or overwrites multiple entry
  pages; documents/notebooks/campaigns generate others independently;
  `content/downloads/index.md` always states that no artifacts are available;
  overview figure insertion depends on an exact heading at line 122.
- **Change:** use the staging plan's publication view for section links,
  document/campaign/notebook indexes, approved download listings, and explicit
  template slots. Retain distinct scaffold versus assembled states. Restrict
  download eligibility by reviewed policy rather than exposing every asset.
- **Accept:** no-source, partial, and full synthetic approval combinations
  produce consistent counts/statuses/links and checksum metadata. Insertion is
  single and deterministic; unsupported source content remains excluded.
- **Risk:** misleading public availability or status claims after a source
  lock changes; preserve known limitations without inference.

### WEB-23 — Route edit/provenance links by page ownership

- [ ] **Evidence:** `overrides/partials/actions.html:2` hides editing only for
  `imported/`, while generated notebook and document pages live elsewhere;
  `pipeline.py:190` generates immutable-commit source/edit URLs. Tests assert
  some literal URLs but not all generated page ownership cases.
- **Change:** consume explicit ownership metadata for website-authored,
  source-imported, and website-generated pages. Keep immutable source links;
  provide an intentional correction route for each page rather than a website
  edit link to a nonexistent generated Markdown file. Review how commit-bound
  edit URLs are presented without introducing mutable provenance links.
- **Accept:** rendered tests for each page kind show correct source/correction
  destinations and never suggest editing staged artifacts. Required template
  behavior survives Material upgrades.
- **Risk:** confusing immutable scientific provenance with the editable branch
  used to propose a correction.

### WEB-24 — Type and validate review manifests before comparison

- [ ] **Evidence:** E04; `source_update.py:117` returns nested `Any` mappings,
  calls a digest regex before checking its type, accepts bool as an int, and
  checks path nonemptiness rather than canonical artifact-relative syntax.
- **Change:** share a versioned typed review-manifest contract with
  `validate_ci.py:60`. Validate exact fields, unique canonical paths, digest
  strings, integer byte counts, and deterministic order before computing a
  pure comparison model. Keep Markdown report rendering separate.
- **Accept:** malformed scalars, root shapes, duplicates, traversal/control
  characters, booleans, and unsupported versions produce domain errors, never
  tracebacks or confusing path displays. Comparisons explicitly disclose
  truncated path lists and retain the complete machine-readable result.
- **Risk:** changing the evidence format consumed by workflows; version changes
  require migration/compatibility tests.

### WEB-25 — Extract source-update proposal lifecycle logic

- [ ] **Evidence:** `.github/workflows/source-update.yml:34–53,259–292`
  embeds proposal discovery, branch association, commit/push/PR creation, and
  recovery in shell; tests mostly assert command substrings and ordering.
- **Change:** extract testable decision functions and narrowly scoped CLI
  orchestration for duplicate/orphan detection and proposal recovery. Handle
  pagination explicitly, distinguish GitHub errors from empty results, and
  parameterize subprocess execution for tests. Keep writes in the proposal job.
- **Accept:** mock no change, active PR, closed/merged branch, orphan, paginated
  responses, partial push/PR failure, cancellation, and cleanup failure. No
  tests create remote branches or PRs. Do not broaden cleanup to unrelated refs.
- **Risk:** hiding privileged operations in a reusable helper; make mutation
  boundaries and authorization visible in workflow and tool interfaces.

### WEB-26 — Bind proposal evidence to validated inputs

- [ ] **Evidence:** `source_update.py:142` writes a report asserting completed
  validation from two supplied manifests; the proposal job reverifies commit-
  only lock differences but does not independently consume a structured
  validation record binding all evidence inputs.
- **Change:** version an evidence envelope identifying website revision,
  baseline/candidate locks and digests, environment, completed checks, and
  artifact-manifest digests. Verify it in the write job before proposing only
  the candidate lock. Treat this as consistency/integrity evidence, not proof
  of scientific approval or authenticity against a fully compromised validator.
- **Accept:** mixed, stale, incomplete, malformed, and tampered evidence fails;
  a report cannot state checks passed when the corresponding record is absent.
  Maintain trusted-checkout isolation and unchanged job permissions.
- **Risk:** overclaiming what checksums or same-workflow artifacts authenticate.

### WEB-27 — Share secret-free local/CI quality checks

- [ ] **Evidence:** `site-check.yml:39`, `validate_ci.py:124–156`, and README
  instructions duplicate check commands. The CI mypy list excludes
  `verify_runner_credentials.py`, although `mypy --strict tools` passes today.
  Source updates repeat website-only checks for baseline and candidate.
- **Change:** introduce explicit source-only and source-backed validation
  stages with one maintained quality target list. Cover all tooling, including
  credential scanning. Reuse website-only results for the same immutable
  website/environment only when provenance proves equivalence; continue
  validating both source-backed artifacts independently.
- **Accept:** local and PR source-only checks require no private credentials
  or source checkouts; source-backed mode retains all gates. Preserve the
  required check name `Validate website source` and fail on new untyped tools.
- **Risk:** collapsing secret-free PR validation into a privileged workflow.

### WEB-28 — Deduplicate workflow setup without merging trust zones

- [ ] **Evidence:** all three workflows repeat Python/cache/dependency setup;
  Pages and source-update repeat token/checkouts, credential-residue ordering,
  and conditional TeX installation. Tests hard-code action SHAs repeatedly.
- **Change:** extract only safe common setup into small local actions or
  documented helpers; keep permissions, environments, token creation, source
  checkout, upload, and deployment explicit at job boundaries. Centralize test
  policy expectations without making the workflow validate itself tautologically.
- **Accept:** structural workflow tests and a workflow linter retain SHA pins,
  main/source-read restrictions, secret-free PRs, residue-check ordering, exact
  artifacts, and separate write/deploy jobs. No remote settings changes.
- **Risk:** reduced auditability or altered credential lifetimes from aggressive
  workflow reuse; duplication is preferable when it preserves a trust boundary.

### WEB-29 — Clarify dependency and toolchain reproducibility

- [ ] **Evidence:** requirements pin selected direct dependencies, not the
  entire transitive environment; PyYAML is imported by core tooling but listed
  under notebook requirements. Document build byte equality relies on a
  separately installed TeX toolchain. `docs/ci-validation.md` calls this a
  reproducible environment without distinguishing these layers.
- **Change:** define bounded runtime/test/notebook/document tooling groups and
  intentional direct imports, with a reviewed constraints/lock strategy and
  environment evidence. Keep numerical pins tied to reviewed source policies.
  Record TeX/font/tool versions for document comparison; clarify cached versus
  fresh installs and advisory audits without promising permanent security.
- **Accept:** fresh source-only and full-mode environments satisfy their own
  declarations; missing imports/stubs are caught; upgrades are isolated from
  this refactoring and cannot auto-update source locks or approval hashes.
- **Risk:** unintentionally recalculating approved results via dependency drift.

### WEB-30 — Simplify stylesheet ownership and layout layers

- [ ] **Evidence:** E09; canonical `docs/stylesheets/readthedocs.css` is 505
  lines of design tokens, Material-specific layout overrides, responsive rules,
  figures, and print styles. `content/stylesheets/extra.css` is unregistered.
- **Change:** document the canonical stylesheet/symlink relationship; remove
  or explicitly archive obsolete styles after confirming no consumers. Group
  layout, component, responsive, and print responsibilities and rationalize
  repeated tokens/selectors without unnecessary file fragmentation.
- **Accept:** retain one authoritative CSS source, mobile/table/figure overflow,
  print content, reduced-motion support, and focus contrast. Verify the allowed
  symlink in both scaffold and staged builds; never replace it with manually
  synchronized copies. Visual/behavior checks belong to WEB-32.
- **Risk:** changing deliberate responsive overrides while reducing repetition.

### WEB-31 — Make browser initialization and MathJax loading robust

- [ ] **Evidence:** `navigation.js:1` initializes on `DOMContentLoaded` only;
  `mathjax.js:11` uses Material's `document$`; MkDocs loads MathJax through the
  mutable major URL `mathjax@3`. Current navigation tests look for strings.
- **Change:** make initialization idempotent with explicit Material lifecycle
  integration and cleanup; distinguish current full-page navigation from any
  future instant-navigation feature. Handle equation-rendering errors/load
  order deliberately. Review exact-version or vendored MathJax delivery with
  license/update documentation rather than silently changing the CDN policy.
- **Accept:** repeated initialization cannot duplicate handlers; Enter/Space,
  Escape, focus restoration, aria state, delayed MathJax load, and repeated page
  rendering work. No scientific math content changes or implicit CSP relaxation.
- **Risk:** treating a currently disabled instant-navigation feature as a
  reproduced bug; lifecycle resilience is a preventive improvement.

### WEB-32 — Replace frontend string assertions with behavior tests

- [ ] **Evidence:** `test_readthedocs_style.py:51–99` checks CSS/JS strings;
  `test_project_overview.py` checks source headings/wording; no browser test
  harness is tracked. These checks do not prove actual focus, contrast, layout,
  equation rendering, search, or generated-page accessibility.
- **Change:** add a bounded browser/DOM verification layer for representative
  scaffold and synthetic assembled pages. Retain scientific qualification
  assertions separately from implementation selectors. Choose any browser
  dependency through an explicit tooling decision.
- **Accept:** desktop/mobile and keyboard routes, menu state/focus, search,
  zoom/overflow, print, headings, alt/caption relations, generated downloads,
  equations, and 404s have meaningful evidence. Record manual signed-out review
  separately; source-string checks alone cannot close it.
- **Risk:** flaky screenshot snapshots or browser tests requiring live private
  sources/network when a deterministic local fixture would suffice.

### WEB-33 — Reconcile current operating instructions with workflows

- [ ] **Evidence:** README calls the site technology/plans prospective, says
  source assembly is deferred, and says the PR workflow uses complete
  validation. `docs/ci-validation.md` correctly describes secret-free PR checks
  versus protected source-backed validation. Local install examples differ.
- **Change:** provide one current development/validation runbook and link to
  it from README/tool docs. Clearly distinguish shell preview, synthetic tests,
  exact-lock source assembly, proposal validation, and deployment. Label known
  source approval states by lock/review date rather than evergreen assertions.
- **Accept:** copyable commands match declared dependencies and maintained
  entry points; no source credentials are needed for PR checks; no text implies
  that passing checks authorizes publication. Preserve historical records.
- **Risk:** changing scientific status while merely updating website guidance.

### WEB-34 — Separate current backlog from historical governance

- [ ] **Evidence:** `AGENTS.md` section 16 lists already-completed foundation
  work; README tells contributors to follow the historical task catalog;
  `docs/codex_tasks.md` labels itself historical but contains obsolete private-
  source PR workflow guidance. `tasks/TODO.md` only lists two small cleanups.
- **Change:** create a clear current-work index and historical archive policy;
  link active instructions to current architecture/operating guidance. Mark
  completed foundation sections as history instead of inviting reimplementation.
  Reconcile owner-decision placeholders with documented outcomes only when
  evidence exists. Do not rewrite old evidence as if it were current.
- **Accept:** a new contributor can locate active work, approval boundaries,
  supported architecture, and completed decisions without contradictory commands.
  Incorporation of this untracked review into tracked governance requires a
  later explicit request; leave these review files untracked now.
- **Risk:** accidentally reviving earlier credential/deployment authorization.

### WEB-35 — Establish bounded lint, typing, and local-file hygiene

- [ ] **Evidence:** `tasks/TODO.md` lists import-order and shebang/mode cleanup;
  CLI files are mode `100644` yet contain shebangs and are used via Python.
  No repository lint/type project configuration is tracked. `.gitignore`
  includes one-off historical names and omits explicit common tool-cache rules.
- **Change:** choose module invocation versus executable-script convention;
  add a narrow reviewed quality configuration and typing coverage for test
  support where useful. Consolidate cache/output ignore policy without
  excluding intended website downloads or source assets. Avoid a broad
  all-rules formatting churn commit.
- **Accept:** quality commands are deterministic in a clean clone; repository
  modes match documentation; import cleanup is behavior-neutral; generated
  caches remain outside tracked files. Do not add ignore rules merely to hide
  these user-requested untracked review notes.
- **Risk:** expanding style enforcement beyond practical maintenance value.

### WEB-36 — Final independent end-to-end and performance acceptance

- [ ] **Evidence:** `test_successful_assembly_is_deterministic_and_preserves_sources`
  compares source snapshots and inventory bytes, not every final artifact byte.
  Archive exports, snapshots, full builds, and quality stages repeat work.
  Hash comparisons in a source-update proposal do not alone prove repeatability.
- **Change:** add a final matrix with EUVICS schema versions, empty/partial/full
  approvals, PDFs, notebooks, campaigns, figures, mixed link forms, failure
  cleanup, and source-update evidence. Compare complete artifact inventories
  across repeated builds with fixed time/environment; explicitly classify any
  approved nondeterministic metadata rather than ignoring whole files.
- **Accept:** all safety invariants and the full suite pass; measured stage
  timing/memory supports any optimization. Cache only immutable inputs and
  never skip source approval or final artifact validation. Verify real locked
  sources and hosted runners only when separately available/authorized.
- **Risk:** optimizing before measuring, or removing verification because it
  is expensive. Performance is secondary to publication safety and traceability.

## Cross-cutting acceptance checklist

- [ ] Existing 130-case baseline remains represented; new regressions cover
      each reproduced gap before its fix.
- [ ] Exact source locks, clean/immutable inputs, deny-by-default publication,
      source attribution, known limitations, and source immutability remain.
- [ ] PR jobs remain secret-free; source-read, proposal-write, and deployment
      trust zones stay separate; required check names and permissions do not
      change without explicit approval.
- [ ] Deterministic builds, exact document checksums, notebook dual execution,
      final-artifact ownership, and privacy scans remain independently checked.
- [ ] Unit tests do not use private content or share production expected-value
      logic; browser/remote/manual checks are reported separately.
- [ ] No scientific calculations, model conclusions, publication approvals,
      production locks, live settings, or deployment actions are changed by
      a supposedly mechanical refactor.

## Items deliberately not proposed as automatic refactors

- Do not replace MkDocs/Material, add a backend, introduce a generic plugin
  system, split this small repository into multiple packages, or duplicate the
  scientific repositories just to change architecture.
- Do not remove the internal canonical CSS symlink as if it were duplicate
  content; E09 confirms it is intentional. Evaluate portability only with
  concrete requirements and preserve one authoritative file.
- Do not refresh `sources.lock.yml` to current upstream heads during cleanup.
  Schema compatibility and scientific publication changes require independent
  source approval and a reviewed lock-update process.
- Do not claim the approved-source notebook process is a secure arbitrary-code
  sandbox. Stronger execution isolation is a design/authorization decision.
- Do not infer that real PDFs, notebooks, or campaigns are approved from passing
  synthetic tests, source availability, or historical plans.
- Do not change GitHub App scope, secrets, organization policy, protected
  environments, branch rules, Pages configuration, or scheduled automation.

## Optional future commit-message template

**Do not use this while the review is intentionally untracked.** If the owner
later explicitly requests tracking these review documents, a suitable message
is:

```text
Record website refactoring review and execution backlog

Documents 36 ordered tasks with evidence, dependencies, and checks.
Records the passing local baseline and reproduced boundary gaps.
Leaves implementation, source locks, and deployment policy unchanged.

Files:
 A  docs/refactoring_20261010.md
 A  docs/exec-plans/completed/031_refactoring-review.md
```

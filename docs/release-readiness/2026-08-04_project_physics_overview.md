# Project-physics overview release review

> Historical URL note (2026-09-02): the website moved to
> `https://pyeuvics.github.io/`. Project-site URLs below record the original
> review environment and are no longer the canonical deployment target.

Review date: 2026-08-04 (Asia/Seoul)

Approval state: **Approved for protected deployment by the project owner on
2026-08-04 (Asia/Seoul)**

## Candidate identity

| Component | Exact candidate |
| --- | --- |
| Website content through Task 5 | `541cb05` |
| Deployed website commit | `e12667fbf46a4fc641577b51bd806106ba41f949` |
| EUVICS source | `f142bd188892f9518a956989ebaf7a42b6930f33` |
| EUVICS manifest | `publication/public-content-v1.json`; 3 approved public-draft inputs |
| pyEUVICS source | `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd` |
| pyEUVICS manifest | `publication/public-content-v1.json`; 53 approved documentation inputs |
| Canonical page | `https://chongshikpark.github.io/euvics.github.io/project/overview/` |

The exact deployment commit will be the reviewed Task 3–5 candidate plus this
release record and the owner's approval record. No scientific page or source
lock may change between approval and that commit without a new review decision.

## Review preview

- Complete assembled overview:
  `/private/tmp/euvics-task5-assembly/site/project/overview/index.html`
- Original vector schematic:
  `content/assets/images/ics-geometry-source-chain.svg`
- Assembled source inventory:
  `/private/tmp/euvics-task5-assembly/staged-content-inventory.json`

The assembled HTML and SVG are complete review artifacts. Interactive browser
preview could not be captured because browser discovery returned no available
browser instance.

## Scientific review

| Review item | Result | Evidence |
| --- | --- | --- |
| Goals versus results | Pass | Opening states that EUVICS evaluates a design and does not claim demonstrated wavelength, yield, bandwidth, brilliance, efficiency, stability, or readiness. Status table distinguishes targets, comparisons, workflow checks, and measurements. |
| Energy and relativistic symbols | Pass | `K_e` is kinetic energy; `m_ec^2`, `gamma`, and `beta=v/c` are defined consistently. The numerical 3 MeV row explicitly says kinetic. |
| Collision and observation angles | Pass | `alpha=0 degrees` is co-propagating, `alpha=180 degrees` is head-on, and `theta=0` is forward from the electron direction. The SVG uses the same convention. |
| Exact linear equation | Pass | Numerator, angular denominator, and recoil term match locked pyEUVICS `docs/science/equations.md` and the approved EUVICS `cdr/sections/source_overview.tex`. |
| Limiting scaling | Pass | `4 gamma^2` is introduced only as the weak-field, recoil-free, head-on, on-axis relativistic limit. |
| Model regimes and controls | Pass | Recoil, `a_0`, polarization, harmonic location, energy spread, divergence, laser bandwidth, aperture, yield, optics, and detector response remain separately qualified. |
| Wavelength versus performance | Pass | The overview explicitly says target-wavelength matching does not establish yield, bandwidth, brilliance, throughput, or detector signal. |
| Validation limitations | Pass | CAIN 6.7 nm remains a known disagreement; 13.5 nm remains provisional; synthetic detector calibration remains a workflow demonstration rather than measured calibration. |
| Citations | Pass with access note | All three DOI URLs resolve to their registered APS destinations. Source/title/DOI identity was independently checked. Publisher pages may return an automated-client challenge, but the citations support Compton-source characterization, general nonlinear Thomson geometry, and nonlinear broadening/brightness limitations respectively. |

## Publication and security review

| Review item | Result | Evidence |
| --- | --- | --- |
| Immutable source locks | Pass | Both locks are exact 40-character commits; exact GitHub commit pages returned HTTP 200 signed out. |
| Allowlisted source boundary | Pass | Production-equivalent inventory contains exactly 3 EUVICS and 53 pyEUVICS inputs with 56 unique staged paths. Task 5 positive/negative fixtures reject missing, excluded, dirty, mismatched, and unlisted inputs. |
| Excluded/private material | Pass | Final artifact scan found no excluded source, secret, credential, internal plan, cost data, private contact, or local machine path. Proposal/CDR PDFs remain excluded. |
| Figure ownership and safety | Pass | The ICS SVG is original website-owned artwork with title, description, long-form alt text, caption, provenance note, no script, no external resource, no embedded data, and no archived or permission-blocked source. |
| Public provenance | Pass | Generated overview names both exact commits and all three approved EUVICS paths. Links use immutable commit trees or assembled allowlisted files, not mutable source branches. |

## Editorial and accessibility review

| Review item | Result | Evidence |
| --- | --- | --- |
| Plain-language opening | Pass | EUVICS, extreme ultraviolet, and inverse Compton scattering are introduced before equations or accelerator-specific detail. |
| Equations and symbols | Pass | Physical picture precedes equations; every equation symbol is defined on the page. MathJax wrappers are present in generated HTML. |
| Logical outline | Pass | One H1 and eight ordered H2 sections; navigation includes the overview exactly once. |
| Tables and mobile behavior | Pass by structural/render evidence | Tables receive bounded horizontal scrolling at mobile width; the SVG uses a bounded mobile scroll width and print fit. Direct SVG renders were reviewed at desktop and mobile-scroll widths. |
| Descriptive links and keyboard behavior | Pass by static evidence | No `click here`; semantic anchors and global visible focus styles are present. |
| Image alternatives and non-color encoding | Pass | Long-form alt text and caption are associated; labels and distinct solid/dashed/dotted line styles duplicate color encodings. |
| Light/dark and complete responsive page | Pending interactive evidence | The SVG has an opaque high-contrast canvas and theme-aware caption; browser discovery returned no browser, so complete page theme, keyboard, desktop, mobile, zoom, and print interaction remain unobserved. |

## Build and deployment review

| Review item | Result | Evidence |
| --- | --- | --- |
| Tests and strict build | Pass | 70 tests passed; strict mypy and targeted Ruff passed; `mkdocs build --strict` passed. Production-equivalent assembly from clean locked source checkouts passed. |
| Project-site base and canonical URL | Pass | `site_url` and generated canonical page use `/euvics.github.io/`. Current public canonical page returns HTTP 200. |
| Intended overview artifact | Pass | Generated overview contains the complete reviewed page, MathJax markup, accessible local SVG, exact provenance, and no placeholder. |
| Link scope | Pass with access note | Local overview/science/Proposal/CDR/navigation/source links resolve in the built artifact. Exact GitHub source commits returned HTTP 200. DOI resolvers returned registered APS destinations; APS challenged the automated follow-up request. |
| Protected workflow | Pass configuration review | Default-branch push runs validation and exact locked-source assembly, uploads that validated artifact, and deploys through the protected `github-pages` environment with least-privilege job permissions. |
| Remote readiness | Pass | Authenticated Git transport pushed the approved history. Public Actions API inspection verified the exact run and jobs despite the separate GitHub CLI token remaining invalid. |

## Caveats and unresolved items shown for approval

- The nominal 3 MeV electron kinetic energy and 800 nm laser wavelength remain
  assumed inputs with approval pending, not measured operating points.
- The 6.7 nm and 13.5 nm values remain design targets, not demonstrated source
  output.
- The 6.7 nm CAIN comparison remains a known disagreement because required CAIN
  provenance and definition matching are incomplete; no empirical correction is
  justified.
- The 13.5 nm case remains provisional without independent simulation or
  calibrated hardware measurement.
- Synthetic detector calibration verifies workflow plumbing only.
- Proposal and CDR PDFs remain excluded pending their independent metadata and
  figure-permission gates.
- The SVG is qualitative and explicitly not to scale; its emission and
  collection cones do not assert numerical divergence or acceptance.
- Browser-based interactive preview and post-deployment signed-out responsive
  review remain unavailable until a browser is connected.
- GitHub CLI authentication remains invalid, but it was not used for this
  release: authenticated Git transport performed the authorized push and the
  public Actions API supplied exact workflow evidence.

## Deployment result

- **Deployment commit:** `e12667fbf46a4fc641577b51bd806106ba41f949`
- **Workflow:** `Deploy GitHub Pages`, run `30862675387`, attempt 1
- **Trigger:** approved push to `main`
- **Validation/package job:** success; completed 2026-08-03T23:35:11Z
- **Protected deployment job:** success; completed 2026-08-03T23:35:25Z
- **Locked EUVICS source:** `f142bd188892f9518a956989ebaf7a42b6930f33`
- **Locked pyEUVICS source:** `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`
- **Live canonical overview:** HTTP 200 signed out
- **Live original SVG:** HTTP 200 and byte-for-byte equal to the approved asset
- **Related live pages:** science, Proposal destination, and CDR destination
  each returned HTTP 200 signed out
- **Live content evidence:** exact source commits, accessible schematic markup,
  CAIN known disagreement, provisional 13.5 nm status, synthetic-calibration
  limitation, and excluded Proposal/CDR PDF notice are present
- **Remaining post-deployment issue:** no connected browser was available for
  interactive desktop/mobile, theme, keyboard, equation, navigation, citation,
  zoom, or print inspection. Static and signed-out HTTP evidence passed.

## Approval decision

Decision: **Approved for deployment**

- **Approver:** Project owner
- **Approval date:** 2026-08-04 (Asia/Seoul)
- **Approved website candidate:** `541cb05` plus this release/approval record;
  no scientific page or source-lock change is authorized without renewed
  review.
- **Approved source locks:** EUVICS
  `f142bd188892f9518a956989ebaf7a42b6930f33`; pyEUVICS
  `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`.
- **Authorization scope:** Commit this approval evidence, push the reviewed
  `main` history, deploy through the protected GitHub Pages workflow, and
  verify the exact deployed commit. Excluded PDFs and existing scientific
  evidence labels remain unchanged.

The project owner explicitly approved the exact candidate after reviewing the
page, schematic, provenance, caveats, source locks, and test/build evidence.
This approval authorizes the normal protected `main` Pages workflow; it does not
approve excluded PDFs or change any scientific evidence label.

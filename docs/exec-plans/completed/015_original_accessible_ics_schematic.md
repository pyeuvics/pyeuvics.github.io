# Original accessible ICS schematic — completed

## Scope

Create and integrate a website-owned SVG that explains the inverse Compton
scattering geometry and the EUVICS source chain without relying on archived or
third-party artwork.

## Boundaries

- Preserve the locked pyEUVICS collision- and observation-angle conventions.
- Do not imply scale, fixed performance, isotropic emission, or equivalence
  between intrinsic emission and collection acceptance.
- Use labels and line styles in addition to color.
- Include no scripts, external resources, embedded data, or editor metadata.
- Do not deploy.

## Plan

- [x] Author a readable, accessible SVG with title, description, geometry,
      acceptance, downstream path, source chain, and provenance note.
- [x] Integrate it into the project overview with useful alt text and caption.
- [x] Add structural, safety, accessibility, and integration tests.
- [x] Validate SVG/XML, strict site build, links, and assembled artifact.
- [x] Render and inspect the vector asset and record any remaining review item.
- [x] Record evidence and move this plan to `completed/` when complete.

## Verification evidence

- `xmllint --noout` passed. Tests verify the SVG title, description, ARIA
  references, required labels, line-style descriptions, and absence of scripts,
  external resources, data URLs, entities, and editor metadata.
- The overview supplies long-form alt text, an `aria-describedby` caption, and
  an explicit statement that collection acceptance does not equal the physical
  emission extent.
- Direct SVG renders were inspected at 1200 × 900 and at the 832 × 624 mobile
  scroll width. Labels, angle arcs, the head-on reference, emission cone,
  collection boundary, source chain, and provenance note are legible without
  relying on color. An opaque white SVG canvas preserves contrast in both site
  themes; mobile CSS provides bounded horizontal scrolling and print CSS fits
  the vector to the page.
- All 67 repository tests passed in 52.83 seconds. Strict mypy and targeted Ruff
  checks passed. `mkdocs build --strict` and `git diff --check` passed.
- Production-equivalent locked-source assembly passed with 56 approved source
  files at `SOURCE_DATE_EPOCH=1785628800`. The website-owned SVG was copied
  byte-for-byte into the final site and passed the artifact scanner.
- No physics-review blocker remains. The illustrated cone and acceptance are
  intentionally qualitative and explicitly not to scale.

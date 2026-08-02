# First public deployment and live review — active

## Scope

Apply the owner’s 2026-08-03 decision to release the currently approved
pyEUVICS documentation while deferring Proposal/CDR PDFs, notebooks, and
campaign artifacts; complete the authorized first protected Pages deployment;
then perform and record the live signed-out accessibility review.

## Boundaries

- Keep all deferred material excluded until its authoritative manifest changes.
- Do not add or repurpose credentials, bypass GitHub protection, weaken
  validation, or claim live checks without browser evidence.
- Do not change scientific content or publication status.

## Progress

- [x] Confirm clean `main` at `b71a2735666f8d0357cb6d04394af62d1a6b94e5`.
- [x] Confirm the first production workflow ran for that exact commit.
- [x] Confirm locked-source artifact validation passed in GitHub Actions.
- [x] Identify the deployment blocker from public job annotations.
- [x] Enable Pages with GitHub Actions as its source through an authorized
      administrator session.
- [x] Rerun the protected workflow and verify its exact commit/artifact.
- [x] Verify the public project URL signed out.
- [ ] Perform browser accessibility, responsive, zoom, print, search, equation,
      navigation, and 404 checks.
- [ ] Update the release report, run final checks, and complete this plan.

## Evidence

- Workflow run `30753297904` validated the exact artifact successfully, then
  failed at `actions/configure-pages@v5` with GitHub `HttpError: Not Found` and
  the instruction to enable Pages and configure it to build with GitHub Actions.
- Artifact upload was skipped and the dependent deployment job did not run.
- The locally configured `gh` account token is invalid, so Codex cannot use an
  authenticated administrator API session to change that setting or dispatch a
  rerun.
- Browser runtime discovery still reports no available browser instance; live
  review remains pending until a browser connection is provided.
- The owner enabled Pages with `build_type: workflow`, public access, and HTTPS,
  then reauthenticated GitHub CLI through the system keyring.
- Because the token could not directly rerun Actions, the reviewed scope and
  authorization record was committed as `42d168b` and pushed to `main`, which
  triggered production run `30753651888` through the normal protected path.
- Run `30753651888` passed locked-source validation, Pages configuration,
  validated artifact upload, and deployment. Official Pages actions emitted
  Node 20 deprecation warnings while GitHub forced Node 24; no step failed.
- Signed-out HTTP checks returned 200 for home, the science entry page, an
  imported equations page, the search index, and the repository stylesheet.
  A deliberately absent route returned 404 as expected.
- R10-001 is resolved. Browser discovery was retried after deployment and still
  reported no available browser; R10-004 remains open pending interactive
  evidence.

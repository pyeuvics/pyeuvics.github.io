# Public Markdown link deployment

## Scope

Update the locked pyEUVICS source to the reviewed public-link cleanup, rebuild
and validate the website, deploy it through the protected default-branch
workflow, and verify signed-out public behavior.

## Decisions

- Lock to pyEUVICS commit `70706d6` because it contains both the 31-link
  cleanup and the hardened empty-alt-image regression.
- Preserve the source publication manifest and its 54-file allowlist.
- Carry the already-reviewed security-hardening branch changes through their
  required pull-request workflow rather than bypassing branch protection.

## Progress

- [x] Update the pyEUVICS source lock.
- [x] Run website tests, strict typing, source assembly, and strict build.
- [ ] Publish through a pull request and protected `main`.
- [ ] Confirm the Pages deployment succeeds.
- [ ] Verify the public imported documentation without authentication.
- [ ] Record evidence and move this plan to completed sequence `00028`.

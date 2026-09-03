# GitHub Pages deployment

`.github/workflows/pages.yml` is the production publication path. It runs only
for pushes to `main` and explicit administrator dispatches. Pull requests remain
covered by the separate read-only, non-deploying `site-check.yml` workflow.

The build job checks out both public source repositories at the exact commits
in `sources.lock.yml`, runs the complete `tools.validate_ci` pipeline, and
uploads only the resulting `.staging/pages/site` directory with the official
GitHub Pages artifact action. The deployment job consumes that same artifact;
it does not rebuild, download another artifact, write a branch, or commit
generated output.

The build job has only content and Pages-metadata read access. Only the
deployment job receives `pages: write` and `id-token: write`. It uses the
protected `github-pages` environment. Both source repositories are private and
are checked out with a short-lived token minted by a GitHub App installed only
on those repositories with Contents read-only permission. Credentials are not
persisted, and a fail-closed scan verifies that no credential material remains
in the runner temporary directory before source-derived validation begins.

## Administrator checklist before the first deployment

- [ ] Confirm both locked private source repositories and commits are readable
      through the repository-scoped, read-only GitHub App.
- [ ] Confirm the post-checkout credential scan passes before source-derived
      validation begins.
- [ ] Confirm the full review artifact and inventory contain only approved
      public material, with expected PDF/notebook/campaign exclusions visible.
- [ ] In **Settings → Pages → Build and deployment**, set **Source** to
      **GitHub Actions**. The workflow deliberately cannot enable Pages itself.
- [ ] Protect the `github-pages` environment. Allow deployments only from
      `main`, require designated reviewers where appropriate, and prevent
      administrators from bypassing the protection unless incident policy
      explicitly permits it.
- [ ] Protect `main` with required pull requests and the successful
      **Site validation / Validate website source** check.
- [ ] Confirm repository Actions workflow permissions remain least-privilege.
- [ ] Restrict Actions to approved sources and require full commit-SHA pins.
- [ ] Set the repository homepage to `https://pyeuvics.github.io/`.
- [ ] Inspect the first workflow's validated Pages artifact before approving
      the `github-pages` environment deployment.
- [ ] Do not manually dispatch the production workflow until the first public
      release is explicitly authorized.

## Signed-out release verification

After an authorized deployment, use a signed-out browser session to verify
<https://pyeuvics.github.io/>. Check canonical URLs, navigation, search, edit
links, root-relative behavior, downloads and checksums, status/limitation notices,
mobile and keyboard behavior, 404 handling, and the absence of restricted
content, credentials, and local paths. Record the workflow run, source commits,
artifact review, approver, and verification result in the release record.

## Rollback

1. Identify the preceding approved deployment and its exact website commit and
   locked source commits from the successful workflow run.
2. Revert the faulty website change on `main` through the protected review
   process. Do not rewrite history or modify generated site output.
3. Let the approved revert push rebuild, revalidate, and deploy a new Pages
   artifact through this workflow.
4. For an urgent incident, an authorized administrator may disable Pages or
   restrict the `github-pages` environment while the revert is reviewed.
5. Verify the restored site signed out and record both the incident deployment
   and the replacement deployment. Never redeploy an unverified downloaded
   artifact or create a `gh-pages` branch as a shortcut.

## External actions remaining

Repository administrators still own Pages-source selection, environment and
branch protection, Actions permissions, repository homepage configuration,
GitHub App installation and Actions secrets, first-deployment
approval, signed-out public verification, and incident rollback authorization.
Adding this workflow does not perform any of those external actions.

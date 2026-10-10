# Workflow setup and trust boundaries

The local `setup-validation` action only selects Python 3.13, restores the pip
cache keyed by reviewed dependency inputs, and installs the declared validation
dependencies. It accepts no credential or source inputs. All external action
references remain pinned to reviewed commits.

- `site-check.yml`: secret-free pull-request/manual source checks; required job
  name **Validate website source**.
- `pages.yml`: explicit protected-main/source-read build, exact source checkouts,
  credential-residue check, conditional document toolchain, validated artifact
  upload, and separate protected deployment job.
- `source-update.yml`: read-only comparison job and a separate proposal writer.
  The writer intentionally keeps its own uncached docs-only setup. Evidence is
  reverified before changing the lock; proposal writes use the explicit lifecycle
  interface with exact owned-branch recovery.

Token creation, source checkouts, TeX installation, uploads, permissions and
environments remain visible in the workflow files. They are not hidden in the
composite action. Sharing setup never authorizes new source content or changes
GitHub settings. Run structural workflow tests and the reviewed actionlint
version when changing these boundaries; record hosted/manual checks separately.

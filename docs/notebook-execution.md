# Trusted static notebook execution

Only source notebooks explicitly approved by the publication manifest and
verified against the exact source lock may execute. Untrusted forks and
arbitrary uploaded notebooks are outside this runner's supported trust model.
Source review, publication approval and the workflow credential boundary remain
required. A temporary HOME, admission regexes and Python audit hooks do not
provide filesystem or network isolation. Native I/O and deliberately hostile
code are not confined; untrusted execution needs a separately approved isolation
design. Do not grant broader credentials to make a notebook pass.

## Inputs and reproducibility

Admission rejects source outputs, ambiguous JSON and skipped execution tags.
Every notebook executes twice in distinct source copies and writable runtime,
home and temporary directories. Neither execution may change its source tree or
the pristine source export. Ordinary Python reads of undeclared data within that
source tree, source writes and unmanaged Python child-process launches fail.
Python imports of source code are permitted; this does not certify the contents
of code constants or provide complete data-access enforcement.

An owned kernel spec launches the invoking Python interpreter. Its package and
source fingerprints, requirement hashes, declared numerical environment policies,
execution limits and guard hash enter the internal execution provenance. Both
executions and their environment fingerprints must match. Python hash seeding is
recorded separately: reviewed notebook code owns Python/NumPy scientific RNG
seeding, and the website injects no scientific seed code.

## Budgets and cleanup

The default limit is 300 seconds per execution, with a 120-second cell timeout,
500 cells and 10,000 kernel messages. Accumulated decoded message bytes are
limited to three times the notebook render allowance, with a 64 KiB minimum and
16 MiB maximum. Writable runtime directories are monitored for at most 512
entries and 32 MiB of regular files; symlinks and special files are rejected.
The original source and final rendered byte allowances also remain enforced.

These are execution deadlines, accumulation limits and monitored file limits,
not hard OS CPU/memory quotas. A message is decoded before its size is checked,
and a writer can exceed a monitored filesystem threshold between observations.
No claim of adversarial resource containment or network blocking is made.

A timeout, resource violation, partial error or cancellation discards the result,
stops the owned kernel immediately and removes its connection/process receipt.
Failed workspaces remain labelled and are never promoted to the requested public
output. Normal output is subject to the same privacy, MIME, raster, link and
ownership checks as the rest of the publication pipeline. Runtime files and
raw execution state are not published as notebook assets.

The trusted read-only build job must retain credential scrubbing and remain
separate from jobs with proposal or deployment write permissions. See
[CI validation](ci-validation.md) and [Pages deployment](pages-deployment.md).

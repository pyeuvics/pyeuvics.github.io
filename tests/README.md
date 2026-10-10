# Website test tiers

Run every tier with `python -m pytest`. Required CI runs the full suite; no
marker or platform selection excludes publication, PDF, or notebook checks.

- `unit/`: parser, path, privacy and contract admission checks.
- `integration/`: synthetic locked-source assembly, links, source immutability,
  real PDF builds, real notebook execution, deterministic output and failures.
- `workflows/`: source-update, runner credentials and CI/deployment boundaries.
- `presentation/`: scaffold configuration, scientific qualifications, generated
  markup, assets and layout checks. `built_site` is a shared session fixture;
  treat its output as read-only. Tests needing mutations build their own output.
- `support/`: independent synthetic input builders and shared repository paths.

Focused directory runs are development shortcuts; they do not replace the
full suite required before completing a task. No private sources are needed.

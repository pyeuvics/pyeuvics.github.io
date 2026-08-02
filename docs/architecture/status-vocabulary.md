# Controlled status vocabulary

## Rules

Status terms are factual metadata claims. They must be taken from approved,
versioned source metadata and supported by the evidence below; page authors and
the assembly process must not infer them from a filename, directory, branch,
date, visual polish, or repository release alone.

A status label answers one dimension only. Publication lifecycle terms do not
prove scientific validity, and scientific-evidence terms do not grant
publication approval. Where both matter, show one label from each applicable
dimension with a nearby explanation. Preserve the source's exact qualification
and known limitations.

## Vocabulary and evidence

| Term | Dimension | Meaning | Minimum evidence |
| --- | --- | --- | --- |
| **Draft** | Publication lifecycle | Content is incomplete or under revision and is not an approved release. | Source metadata marks the exact version/commit as draft, identifies an owner, and permits public draft publication. |
| **Approval Pending** | Publication lifecycle | Review or approval is required and has not yet been recorded. | Source metadata identifies the pending decision and responsible owner; a publication manifest must separately permit any public placeholder. The underlying unapproved artifact stays excluded unless explicitly allowlisted for public review. |
| **Released** | Publication lifecycle | A specific immutable version has been formally made public. | Authorized release record with version/revision, date, source commit, owner approval, applicable license/permissions, and checksum for downloadable artifacts. |
| **Superseded** | Publication lifecycle | A previously published version has been replaced and should not guide current use. | Source metadata names the replacement and records the supersession decision/date. Keep the old item only when its manifest authorizes archival publication. |
| **Design Target** | Claim type | A desired or specified design objective, not evidence that it was achieved. | Approved requirement/design source gives the value, units, conventions, scope/configuration, revision, and authority/status. |
| **Calculated** | Evidence type | A result produced analytically or numerically from a stated model, not by itself a simulation or validation. | Reproducible source identifies model/equations, inputs, units, assumptions/approximations, software/version if used, configuration, and limitations. |
| **Simulated** | Evidence type | A result produced by a defined computational simulation. | Reproducible source identifies code and version/commit, configuration/input, seed where relevant, execution policy, model assumptions, and limitations. |
| **Reference** | Evidence role | An approved comparison case or benchmark definition; it is not automatically validated. | Versioned source defines the case, provenance, parameters with units/conventions, intended comparison scope, and approval for reference use. |
| **Validated** | Validation state | A specified claim/model/version has met explicit acceptance criteria within a stated domain. | Reviewed validation record identifies subject/version, comparator or evidence, method, criteria, configuration/domain, quantitative result, approver, date, and remaining discrepancies/limitations. |
| **Unvalidated** | Validation state | No applicable completed validation evidence is recorded, or the evidence is insufficient for the stated use. It does not mean false. | Source metadata explicitly records the absence/scope gap or a review shows required validation evidence is missing; state the affected claim/version/domain and known limitations. |

## Badge policy

Badges may be used only on page titles/metadata blocks, document and download
cards, campaign summaries, validation summaries, and comparison tables where
the badge's subject is unambiguous. The same controlled spelling is used in
navigation-adjacent summaries, legends, and filters.

Each badge must:

- be backed by the exact source evidence and locked commit;
- expose the term as text, not color alone, with sufficient contrast;
- have a nearby explanation or link to evidence, scope, and limitations;
- identify its subject when multiple artifacts or claims appear together;
- remain legible in high contrast, grayscale, mobile, and print/PDF output.

Badges must not appear as decoration, in primary navigation labels, or as a
substitute for provenance and limitations. A page must not receive a single
status that silently applies to unlike claims. `Released` must never be treated
as `Validated`; `Reference`, `Calculated`, or `Simulated` must never imply
achievement of a `Design Target`.

If evidence is missing or contradictory, exclude the claim or artifact and
record the owner decision required. Do not automatically apply `Unvalidated`
as a catch-all: use it only when its scope is source-backed; otherwise say that
validation status is unresolved in internal review material and do not publish
the badge.

## Examples of valid combinations

- A publicly reviewable document can be `Draft` and contain a `Design Target`.
- A released campaign report can be `Released`, with individual results marked
  `Simulated` and a separately scoped comparison marked `Validated`.
- A benchmark can be `Reference` and `Unvalidated` if the source explicitly
  supports both statements for the stated domain.

These examples define semantics only; they assign no status to any EUVICS or
pyEUVICS material.


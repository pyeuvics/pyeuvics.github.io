# WEB-05 — Strict structured inputs

## Scope
Reject duplicate keys, non-string mapping keys, boolean/float schema versions,
non-finite values, invalid encodings and impossible/noncanonical dates with
domain errors. Preserve supported EUVICS 1.0/1.1 and pyEUVICS 1.0 inputs.

## Progress
Sixteen new cases reproduced validation or exception-shape failures before
implementation; all 22 targeted cases pass afterward. Strict JSON/YAML readers
reject ambiguous mappings, invalid UTF-8 and non-finite values; source schema
versions require integers rather than bool/float equality. Both source approval
dates and document dates require real, canonical ISO calendar dates. Invalid
candidate status containers and mixed keys now raise ContractError.

## Verification
172 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.

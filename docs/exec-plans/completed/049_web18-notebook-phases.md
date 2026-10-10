# WEB-18 — Separate notebook admission, execution and presentation

## Scope
Introduce typed admitted/executed/rendered notebook results. Separate source
admission, real execution, output/MIME/resource validation and page rendering.
Move campaign presentation out of the execution module. Preserve dual execution,
source immutability, publication inventory and shared browser content policy.
Normalize rendered notebook headings while preserving scientific cell text and
code. Require a single page H1 and owned raster output paths.

## Decisions
Keep the current execution environment and limits for WEB-19/20 to address in
order. Tests may mock execution only at unit boundaries; all real-kernel
integration cases remain enabled. Source and rendered byte limits are checked
before parsing/copying where applicable. Resource names must be canonical paths
inside the notebook's reserved output directory. Images use WEB-16 inspection.

## Progress
Typed admitted, executed and rendered results separate policy, execution, MIME/resource handling and presentation. The facade retains two real executions and exact output comparison. Admission reads bounded source bytes with strict JSON checks; rendering validates raster bytes and canonical names inside the reserved notebook namespace before staging. Renderer-verified heading edits shift real headings while preserving scientific prose, link destinations and literal code examples; final notebook pages have one H1. Sixteen new phase tests cover headings, invalid MIME/resources, admission without execution and bounds after normalization. All existing real-kernel, source immutability, nondeterminism and output-limit integration cases remain enabled. Kernel identity and total execution resource policy remain the next two ordered tasks.

## Verification
455 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.

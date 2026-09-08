# Paraphrase coverage audit — 2026-09-08

**Latest follow-up:** [round eight](ROUND8-RESULTS.md) improves bounded preference
edits under fresh target sampling, but both baseline and candidate fail all 52
complete-intent checks in a separately authored natural-language corpus. The
earlier blanket concern remains material; the new opening grammar does not
establish broad semantic interpretation.

**Follow-up:** the [round-six repair](ROUND6-RESULTS.md) fixes the recorded
black-to-white failure and passes fresh aggregate accuracy validation on 2,800
targets across official, new-form, mixed and limited attribute-paraphrase suites.
The audit below describes the pre-repair `fa359373` snapshot. Its broader warning
about unrestricted language coverage remains applicable.

**Finding: paraphrasing was considered and bounded repairs were validated, but
general paraphrase robustness has not been established.** Earlier review text
treated identical private wording too confidently. This audit corrects the
assumption; it does not change the active agent or claim a new benchmark score.

## Source boundary

The [saved specification](../competition_specification.md) says: "If
natural-language paraphrasing is added by the organizer, it cannot decide
correctness." Product hits remain exact identifier matches regardless of prose.

The user-supplied workshop transcript at `/Users/limzichao/Downloads/message.txt`
says no undisclosed natural-language paraphrases would be introduced, and that
updated templates/examples would be published before the submission deadline.
That is a workshop assurance, not a reason to omit language-shift validation.
The original Lark page could not be reopened through the web tool during this
audit, so no fresh confirmation of the live specification is claimed.

## What actually runs

- `intent.py` maps a bounded set of regular-expression sentence forms into the
  existing state reducer. Unrecognized text becomes untyped free-text evidence.
- BM25 and BGE provide lexical and semantic retrieval when wording is unsupported.
  The embedding model does not perform structured intent extraction or retract
  obsolete requirements.
- `service.py` recognizes protocol events from the original message, separately
  from the intent reducer's normalized form. A recognized intent paraphrase is
  therefore not necessarily eligible for exact transcript replay.
- Unsupported protocol wording disables exact consistency for that transcript;
  ordinary search continues. Continued operation is not evidence of equal
  recommendation quality or preserved protocol-planning benefits.

## Reproduced state-level diagnostics

These are five hand-written diagnostic cases, not a representative accuracy
suite. They call the active default `apply_user_message` and
`recognize_protocol_observation` implementations at source commit `fa359373`.
No catalog retrieval, target labels or end-to-end hit measurements are involved.

| Message or sequence | Actual state / recognition |
|---|---|
| `I'm looking for Shoes. A key requirement is: Color: black.` | Category `Shoes`, typed `Color: black`; recognized initial protocol event. |
| `Please help me find Shoes. It must have Color: black.` | Correct category and typed requirement; protocol observation unsupported. |
| `Could you help me pick shoes? I need them in black.` | Category unset; entire message becomes untyped free text; protocol observation unsupported. |
| Official opening above, then `Actually, ignore my earlier preference. What I need is: Color: white.` | Black removed, white becomes the active typed override. |
| Official opening above, then `Make that white instead; black is no longer what I want.` | Black remains an active typed initial requirement; correction is appended as untyped free text. |

The last case demonstrates a state-management defect. Its rendered dense query
still contains `Attributes: Color: black` alongside the correction. It does not
establish that the final recommendations fail on every such message.

## What previous validation establishes

The `paraphrase` and `punctuation_variants` functions in
`scripts/benchmark_finalists.py` preserve every catalog-derived value verbatim.
They alter sentence scaffolds with a small fixed set of transformations; some
messages are unchanged. Round-four fresh targets improve the evidence about
those particular forms, but the forms themselves were developed and known.

Fresh category-balanced language 800 improved HR from .847500 to .986250 and
score from .748951 to .922438. Fresh weighted-language 1,600 improved HR from
.821250 to .965625 and score from .722505 to .888442. These are the existing
[round-four results](ROUND4-RESULTS.md), not new runs.

They do not validate held-out sentence families, synonymous attribute values,
implicit category names, varied negation/retraction, pronoun references, or
mixed exact-template and free-form turns. No causal ablation establishes that
our embeddings make us superior to a competitor on these cases.

## Required next accuracy work

1. Evaluate meaning-preserving variants while keeping the same latent intent,
   disclosure sequence and target. Hold out both targets and wording families;
   merely sampling more products under the same transforms is insufficient.
2. Include attribute paraphrases, initial category phrasing, clarification,
   no-preference, exclusions and corrections, plus mixed-language-form sessions.
   Review transformations for semantic equivalence; do not silently introduce
   new preferences or lose existing ones.
3. Compare structured state and per-scenario HR/MRR/turns, alongside aggregate
   results. Include negative controls where negation or a correction really
   changes the meaning; these must not normalize to the old intent.
4. Develop catalog-grounded semantic extraction with explicit add/replace/remove
   operations and provenance. Uncertain interpretations should remain soft or
   trigger clarification. Do not grant exact simulator-replay authority merely
   because text is similar to a template.
5. Freeze the candidate before fresh validation. Apply the agreed aggregate
   accuracy acceptance rule to original and paraphrased suites, report the
   language conditions separately, then optimize runtime after accuracy passes.

The diagnostic cases above are now development examples and must not be called
unseen validation in future work. This audit adds documentation only; it does
not implement the semantic extraction work or promote a new runtime policy.

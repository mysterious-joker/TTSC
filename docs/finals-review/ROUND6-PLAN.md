# Round six: compositional intent repair

Baseline: personal commit `fa359373a632f07ec9caf494edfbbc4d8a2ab13f`.
Work is isolated in the personal fork. This addresses the
[paraphrase audit](PARAPHRASE-AUDIT.md), with accuracy prioritized before runtime.

## Candidate boundary

Add a bounded intent-operation reducer for unsupported prose, with explicit
add, replace, withdraw, exclude and clear operations. Ground destructive edits
in an existing value or typed slot. Retain unrelated confirmed requirements and
mark untyped interpretations soft while preserving their revocable provenance.
Interpret explicit replacements before the old polite-answer recognizer.
Incomplete or uncertain interpretations fall back atomically. This does not
alter protocol event recognition, retrieval models or ranking policies.

The development suite reuses 200 consumed targets under newly authored forms.
Its initial result improves HR .835 → .910 and score .730936 → .821754, with
37 session regressions and weaker browsing/boundary mean utility. These are
selection diagnostics, not fresh evidence. Further pre-freeze edits address
unit-test correctness and ambiguous syntax, not target-specific outcomes.

Runtime freeze SHA-256:
`867c55b8e570cd399c061efd087b46889c0313b0629ec986c3968ad853e58939`.
The complete per-file map and timestamp are in the local
`round6/runtime-freeze.json`; the final result bundle embeds that map.
427 unit tests passed before the freeze. Runtime source remains frozen through
confirmation. New wording transformations were authored after this freeze and
then frozen before opening their evaluation results.

## Fresh validation

Seed `202609087`; exclude all 18,600 prior/reserved target IDs found in the
recorded research input paths. The 2,800 new targets are mutually disjoint.
Profiles are sampled independently of targets. The agent sees neither target
identifiers nor scenario labels. The wrapper transforms only the user message;
the official evaluator still controls interaction and exact-ASIN correctness.

| Suite | Targets | Distribution / wording |
|---|---:|---|
| Official | 400 | Uniform targets; unchanged evaluator messages |
| New forms | 800 | Square-root-review-weighted targets; new sentence forms |
| Mixed | 800 | Weighted targets; deterministic mix of original and new forms |
| Attribute language | 800 | Category-balanced targets; new forms plus limited reviewed attribute equivalences |

Require nondecreasing aggregate HR, MRR and turn efficiency on every suite,
identical complete responses on the official suite, a positive one-sided paired
score-gain bootstrap bound at alpha .05/8 on each language suite, and zero
exceptions/invalid outputs. Run all suites once without interleaved tuning;
report failed gates. Do not pool development results into confirmation.
Runtime measurements during overlapping jobs are diagnostic only and are not
part of this accuracy-first promotion gate.

The new forms exercise combinations of the same language operations; they are
authored by the same coding agent, not an independent human language study.
Attribute transforms include color-label paraphrasing, grey/gray spelling,
material phrasing and a few exact care/material equivalences. Most long feature
descriptions remain verbatim. This is a broader sensitivity test, not a claim
of representative unrestricted English or the organizer's private distribution.

Additional checks reproduce public and previous controlled-language results.
21 post-freeze state cases combine new color/material values with replacement,
retention, hypothetical and negation cases. They are diagnostic checks, not a
statistical estimate of language accuracy. After this run all exposed cases and
wording families are development evidence for any later candidate.

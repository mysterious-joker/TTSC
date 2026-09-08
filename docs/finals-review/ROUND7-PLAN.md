# Round seven: provenance-aware attribute index experiment

Baseline: personal commit `c3a18924ffbef04e11b377a06f46d19cfb012628`, including
the accepted language repair. The user's new condition restores response-time
non-regression as an acceptance requirement for this experiment.

## One focused candidate

Build an offline SQLite attribute sidecar from the frozen catalog. Explicit
detail fields provide stronger evidence; title/feature mentions provide weaker
evidence. Store source field and polarity. Word boundaries and local negation
prevent `cotton-free` or `blueberry` from becoming affirmative cotton/blue facts.
Missing attributes are unknown. Opposing observations are conflict, not proof
that either side is true. Single color/size values do not prove that a parent
product has no other variants. Reuse existing category and price handling.

The only initial ranking experiment is a stable tie-break within the existing
exact ranker's best evidence tier, and only after unsupported wording has
disabled exact protocol consistency. Prefer affirmative field evidence, then
weaker text evidence; negative observations count as counterevidence. A conflict
contributes zero. Missing values also contribute zero. Preserve the candidate
set, all other tiers, existing ranking policies, and truthful belief ordering.
No new hard filter is introduced. No product-specific weights or target labels
may enter the sidecar, query extraction or scoring code.

The sidecar stores indexed bitmaps so each query retrieves attribute postings
instead of scanning product descriptions. It is bound to the catalog hash and
schema version. Missing, stale or failed indexes must preserve baseline behavior.
The production adapter remains unchanged while the experiment is evaluated.

## Evidence boundaries and acceptance

Current catalog audit: all 50,000 rows have a details dictionary, but explicit
Color occurs in 2,439 rows, Material in 2,069, and Size in 925. Absence cannot
support a negative decision. `Department`, manufacturer and package dimensions
must not be mislabeled as shopper-requested material, brand or wearable size.

First verify provenance, negation, conflicting fields, missing metadata,
compound material composition and stale-index fallback using controlled tests.
Then compare the candidate with the current baseline on public 200 and consumed
language development data. Freeze runtime/experiment code before sampling fresh
targets or observing their outcomes. Fresh confirmation includes paraphrased
requests, overrides and metadata suppression. Every scored recommendation must
still be a valid original-catalog parent ASIN.

Require aggregate HR, MRR and turn efficiency not to decrease on every suite,
statistically supported language score gains using a one-sided paired bootstrap
with alpha .05/4, and zero contract errors. Public original-wording responses
must remain identical. If accuracy passes, require non-increasing median
end-to-end and p95 response time in three alternating fresh-process pairs; do
not advertise timing from overlapping jobs as a speed improvement. Rejected
experiments remain opt-in research code and are not enabled in the active agent.

The referenced GitHub pages could not be fetched through the web tool in this
session. The implementation is independent and grounded in the local code and
catalog; this plan does not claim a fresh verification of `yl-dev` source.

## Development amendment before fresh results

Field-first ties preserve HR .91 but reduce MRR .666704 → .636579 and score
.811811 → .803874 on 200 consumed targets with attribute-language transforms.
136 ranking interventions occur with zero internal errors. This suggests that
documentation completeness is not a reliable tie-break in this population.

Add one narrower candidate: counterevidence-only tie-breaking. Positive evidence
and unknown both contribute zero; explicit opposing observations may demote a
candidate within the same tier. No candidates are removed. This directly tests
the negation benefit without rewarding better-filled metadata.

There are now two hypotheses. Correct fresh paired score bounds to alpha .05/8.
Freeze both candidates before fresh results, run each once on public 200,
800 new weighted language targets and 400 separate targets with explicit detail
fields suppressed in the sidecar. The target sets include ordinary overrides
under the fixed 40/40/15/5 scenario mix. Compare each with baseline. The suppression
stress changes only the new sidecar: the shared retrieval catalog, embeddings
and evaluator retain the original metadata. It does not simulate losing all
metadata from the complete agent. Run the original failed development arm in
fresh validation as a replication; it is not eligible unless all gates pass.

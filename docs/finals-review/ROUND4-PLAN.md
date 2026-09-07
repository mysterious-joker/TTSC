# Round four: early decisions and distribution uncertainty

Baseline: personal branch commit `1ef7440`, including the accepted caches.
All earlier 800 development, 1,600 confirmation and public/stress results are
consumed evidence. None is described as a fresh holdout in this round.

## Declared hypotheses, before running the new arms

1. `support_cold_prior`: revisit the existing category-only first-turn prior
   under the user's aggregate rule. No change to its previously tested logic.
2. `first_turn_prior`: use catalog review-count ordering only on the initial
   turn, retaining baseline ranking for every later disclosure and correction.
3. `soft_prior`: give the existing catalog prior two reciprocal-rank votes and
   the semantic/lexical order one vote, only within complete transcript support.
   The fixed 2:1 choice is a hypothesis, not a fitted optimum or probability.
4. `recoverable_prior`: change the first probe only when both the baseline
   probe and the more popular alternative have unique, disclosing replies to
   the baseline question. Retain that question and all other relative order.
   Exclude pending overrides, initial browsing/boundary ambiguity, final turns,
   incomplete supports and baseline widths above one. This is a structural
   recovery condition, not a guarantee on all future implementation behavior.

No product/session IDs, target labels or public-set lookup enter an arm. No
parameter sweep or best-seed selection. Research arms remain opt-in.

## Acceptance and validation

Screen all four on the consumed development 800 and public 200. Aggregate HR,
MRR and turn efficiency must each not regress on either suite. Individual
losses remain diagnostic. This is a screening condition, not proof of gain.
Eligible arms also face the existing language stress suite.

Distribution sensitivity is assessed with fixed target-disjoint samples:
uniform products, square-root review-count weighted products, and uniform
coarse categories then uniform products. These are three plausible synthetic
stress distributions, not claims about the organizer's hidden sample. Profiles
are sampled independently and do not model purchase correlation.

Generate all fresh data once, exclude public targets and every target in the
previous frozen 2,400, and partition targets without overlap. New development
uses 800 popularity-weighted and 800 category-balanced targets. Reserve 1,600
uniform, 1,600 weighted and 800 category-balanced targets for confirmation.
The new development results may reject an arm, but cannot silently redefine it.

Only a candidate passing development/public/stress reaches confirmation, after
its code and data hashes are frozen. Require non-regression of all three metrics
on every confirmation suite, and a positive paired-bootstrap score lower bound
on the equally weighted mixture of the three suites. Use family size four for
the declared accuracy hypotheses, and report each suite separately. Equal
weighting is a declared robustness objective, not a hidden-distribution estimate.
Runtime includes startup plus evaluation; use three sequential alternating
baseline/candidate pairs and require non-increasing total time and p95 latency.
Do not tune after opening confirmation. Preserve rejected results.

If these hypotheses fail, diagnose the failed mechanism before declaring any
new follow-up. No accuracy-changing code is promoted merely to improve a public
score screenshot. A championship cannot be guaranteed by these measurements.

## Input-distribution audit during screening

Catalog review-count medians: public targets 6,846; old uniform development 12;
new square-root-weighted development 130.5; new category-balanced development
13. This is an input-feature audit, not use of held-out outcomes. The workshop
transcript describes targets selected from eligible historical purchase/review
records, rather than uniformly from the catalog. Consequently, uniformly drawn
targets test broad catalog coverage but cannot establish hidden-score dominance.
The square-root weighted suite is also much less popularity-concentrated than
the public data. None of these synthetic distributions is claimed to reproduce
the private selection procedure. We do not reconstruct its eligible target pool.

Two screening jobs may overlap to reduce research wall time. Their latencies
are diagnostic only; acceptance timing, if reached, remains sequential.

## Declared structural follow-up after the four screening failures

All four initial candidates failed at least one aggregate metric: cold prior
loses three total turns on new category development; first-turn prior loses old
development MRR and turns; soft prior loses old development turns; recoverable
prior loses three old development turns. Confirmation remains unopened.

Two additional, fixed hypotheses follow from the recovery mechanism rather than
from product-specific winners: `ambiguous_probe` and `cold_ambiguous`.
The first displaces a baseline probe that is uniquely identifiable after the
baseline question with a more-popular candidate whose answer remains ambiguous.
This directs the current guess toward a product that may otherwise take multiple
turns to resolve, while the displaced candidate remains identifiable after one
answer. Preserve the question, limit support to 200, and exclude pending
overrides and initial browsing/boundary ambiguity. Prefer the largest remaining
reply group, then the existing catalog prior; do not tune a count threshold.
The second combines that rule with the unchanged category-only cold prior.
They face all the same screening and confirmation requirements. Increase the
accuracy hypothesis family to six, including every failed earlier candidate.

## Final ranking hypothesis and independent exact pruning hypothesis

Both ambiguity variants pass old development and new weighted development but
lose category-development turn efficiency (one and four total turns). Their
confirmation remains unopened. The final ranking arm is `dominant_prior`: use
the uniquely recoverable baseline-probe guard, but require the proposed product
to have at least ten times `(1 + baseline review count)` reviews after adding
one to its count as well. Choose the first such product in catalog-prior order.
The tenfold margin is declared as an order-of-magnitude prior hypothesis, not
calibrated confidence and not a fitted optimum. It can select an ambiguous or
uniquely recoverable alternative; the displaced baseline probe must still be
uniquely recoverable. Include all seven hypotheses in statistical correction.
No further margin search follows its result.

Independently, test an exact planner pruning optimization: if exposing a prefix
already gives one of its members less utility than the baseline continuation,
the question cannot rescue that immediate hit. Skip that width and every wider
prefix. This must retain every decision, including tolerance and tie behavior.
Validate against the previous exhaustive implementation on randomized complete
beliefs and all frozen response digests before adoption. No scoring rule changes.

## Separate language robustness intervention

All seven ranking arms fail a development aggregate. No ranking arm will be
promoted, and the 4,000 confirmation targets remain unused at this point.
Source inspection identified ordinary envelope parsing gaps: punctuation after
`must have`, sentence/dash separators in `change of plan`, an explicit tentative
preference after `help me find`, uncertainty in a second opening sentence,
`my priorities are`, and `any ... is fine with me`. Add these to the existing
anchored intent grammar while preserving literal payloads and intent provenance.
This changes free-form intent reduction, not exact-protocol recognition. It
does not claim arbitrary natural-language understanding or add simulator
privileges to paraphrased conversations.

Screen the existing paraphrase suite and a separately defined punctuation
variant suite on the new weighted development targets. All HR/MRR/turn metrics
must not regress. Official public/development responses must remain identical.
Freeze the complete code and wording transforms before opening confirmation.
Use the reserved uniform 1,600 with official wording to verify unchanged
behavior, weighted 1,600 with punctuation variants, and category 800 with the
earlier paraphrase envelope. These three target sets remain mutually disjoint.
Require aggregate non-regression on each, a positive paired score lower bound
on the language confirmation mixture, and sequential three-pair runtime and
p95 non-regression. Family size eight counts the seven ranking hypotheses and
this language hypothesis. If language fails screening, keep it disabled and
evaluate the independent exact pruning change alone.

## Completed validation disposition

The final validator required a positive score-gain bound on **each** language
suite, which is stricter than accepting only the proposed mixture bound.
Both passed, as did unchanged official responses and all runtime/p95 gates.
The candidate stayed frozen throughout confirmation. See
[ROUND4-RESULTS.md](ROUND4-RESULTS.md) for the adopted repair/pruning, disclosed
individual and subgroup losses, and the seven rejected ranking alternatives.
The confirmation targets are now consumed.

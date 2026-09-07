# Second research round — frozen before candidate measurements

The target is HR@10, MRR and TechnicalScore approaching 0.99. MTTC is minimized,
not maximized. No universal improvement guarantee is assumed.

Baseline remains `08cd1f1`, with the submission runtime inherited unchanged from
the preserved finalist working tree. The original 800 development targets are
consumed development data. The original 1,600 confirmation targets remain sealed
until a candidate passes the original strict non-regression gate.

Four independent hypotheses, no parameter sweep or public-label exceptions:

1. `support_cold_prior`: order the entire exact transcript support by catalog
   review count on turn one when there are no active requirements/exclusions.
   Unlike round one's bounded reranking experiment, this also selects the pool
   from the full support before truncation. Preserve exact-evidence tiers.
2. `support_review_prior`: use that prior for every exact transcript support.
   This tests whether generic retrieval rank is misleading once exact replay has
   already established candidate compatibility. Preserve evidence tiers.
3. `answer_value`: evaluate every legal question against the complete surviving
   support after the current rank-one probe. Select the highest expected next
   turn official reward with uniform candidate weights; retain current order.
4. `two_step_value`: optimize the next question and output width over two reply
   transitions, with exact enumeration for exhausted groups. Use a bounded
   200-product complete support; larger supports use the one-step question rule.
   This tests deeper interaction planning rather than fitted retrieval weights.

These are independent implementations of published mechanisms and new research,
not reproductions of ARC/Fable7, whose repositories are inaccessible. The question
models use visible catalog cards, not actual target/session/scenario labels.
Uniform posterior and preserved future ranking are explicit approximations.
Unrecognized dialogue and pending overrides retain the baseline planner.

All four are screened against the same baseline on the development 800, with
paired bootstrap alpha 0.05/4. Promotion still requires strict score gain, no
individual utility loss, no lost hits, no scenario harm, no errors/invalid output,
and no language-stress regression. A higher aggregate score alone is insufficient.
Public 200 runs are diagnostic only. No rejected candidate is enabled by default.

A separate catalog-only oracle audit estimates observability limits with the
entire disclosure signature granted at turn one. It is an optimistic bound under
uniform target sampling, not a hidden-score estimate and never an agent input.

## Follow-up declared after the first three arms were measured

`counterfactual_shield` addresses the observed question-planning regressions by
replacing the fixed future order assumption with rollouts through the actual
unchanged baseline `respond` implementation. Propose the one-step question, then
compare it against the baseline for every exact surviving catalog hypothesis.
Admit only a strict mean gain with no per-hypothesis utility loss. This is a new,
exploratory hypothesis, not one of the four original screens. No individual
development target or failure is used to define the intervention rule.

Bound it to 2–200 complete survivors on turns 1–8, no pending override, and an
exact protocol planner action. Clone session memory while retaining immutable
backend assets and snapshot-token identities. Branch by the exact rendered reply;
refusal/disclosure handling follows reconstructed catalog cards. Limit each
certificate to 512 baseline calls; reject on exhaustion, errors or discrepancies.
All normal-language and larger-support states preserve the baseline. Instrument
accepted/rejected proposals, simulation calls, budget rejections and errors.

The model does not cover an unannounced future override or new simulator behavior.
This is a conditional, catalog-world safety check, not a universal guarantee.
Development uses the stricter five-hypothesis bootstrap bound. Confirmation is
still reserved for a clean development and stress pass.

The initial shield diagnostic restricted activation to turns 2–8 and proposed
zero changes. Before further measurement, the guard was extended to turn one:
the existing planning lock already excludes ambiguous browsing/boundary openings
and pending overrides. An exact buying opening has ordinary deterministic replies
from its first turn. This is a structural coverage change, not a target exception.
The first diagnostic is retained as `shield-turn2-noop.json` in ignored output.

The 24-survivor variant tested only two proposals and rejected both. Its output
is retained as `shield-small-support.json`. The final coverage guard uses the
existing runtime's 200-candidate completeness bound, rather than introducing a
separate 24-item threshold. The fixed 512-call budget still bounds simulation;
no actual target, scenario, or sample ID controls activation.

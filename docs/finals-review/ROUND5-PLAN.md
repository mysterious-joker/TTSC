# Round five: early ranking and question interaction

Baseline: `26866df`, including the accepted round-four intent repair and pruning.
All prior public and synthetic results are consumed. No competitor or private
target labels enter the agent. Work stays in the personal fork.

## Fixed hypotheses before measurement

1. `language_top1`: on a transcript outside strict protocol recognition, request
   rank one before turn ten. Keep the actual returned prefix in session memory;
   never trim a response after recording a larger displayed slate. Retain the
   complete permitted final-turn prefix. This tests Kopi's output-width idea on
   our improved intent/retrieval path, without changing exact protocol sessions.
2. `cold_answer`: category-only initial review prior combined with the existing
   one-step answer-value question. Earlier independent experiments changed one
   component at a time; this tests their interaction without fitting weights.
3. `first_answer`: all first-turn review prior combined with that same question
   rule. Later rankings retain the baseline fusion/evidence policies.
4. `cold_continuation`: category-only initial prior with the previously tested
   full-continuation question model, preserving candidate ordering. This tests
   whether better questions offset the observed cold-prior turn cost.

Use family size five: four hypotheses and at most one combination of a passing
official-policy arm with a passing language-width arm. No parameter/seed sweep.
The choice between passing official arms uses aggregate development score only.
No combination is eligible if either component independently fails screening.

## Screening and confirmation

Screen on public 200, old uniform development 800 and the current language stress
200, using identical data/evaluator and unrounded paired outcomes. Require each
suite's aggregate HR, MRR and turn efficiency not to decline. Individual and
scenario losses are reported. Official unchanged behavior is acceptable for a
language-only improvement, and unchanged language is acceptable for an official
improvement. Every claimed accuracy gain needs a positive multiplicity-adjusted
paired-bootstrap lower bound. Previously consumed round-four weighted/category
development further checks distribution sensitivity before confirmation.

Screening may overlap processes; its timing is diagnostic only. A surviving
candidate must run three sequential alternating process pairs against an archive
of this baseline, with non-increasing median total time and p95 and a positive
paired session-saving lower bound for any speed claim. Do not substitute a faster
unrelated historical run as its baseline.

Generate new confirmation targets once, excluding the public 200, old 2,400 and
all round-four 5,600. Freeze code, wording and data identities before opening
outcomes. Include uniform and review-weighted official sessions and separate
controlled-language sessions. These are sensitivity distributions, not the
organizer's hidden 800. If no hypothesis passes screening, do not consume new
confirmation or alter the accepted runtime. Record the failed mechanisms.

## Follow-up after language-width screening

`language_top1` loses seven hits and .054 turn efficiency despite higher MRR.
Keep the original width policy. Inspection shows ordinary exact-evidence ranking
uses original retrieval rank before popularity, so popularity cannot resolve a
tie when original ranks are unique. Test `language_prior`: order ordinary
candidate inputs by catalog review count, then apply the unchanged exact-evidence
ranking, keeping all widths and exact protocol behavior. This evaluates Kopi's
prior idea without the failed width restriction. No coefficients are fitted.
The hypothesis family becomes six, retaining the unused conditional-combination
slot and all four original hypotheses. No confirmation has been opened.

## Vector-valued continuation after weighted screening

Both cold-prior/question combinations improve public, old uniform and category
aggregates, but lose weighted-development MRR by .000833333. Scalar expected
utility permits component trade-offs that the user's gate forbids. Declare
`cold_vector`: keep the category-only cold prior, but admit a question only when
the modeled continuation's total hits, reciprocal ranks and turn efficiency are
each at least the modeled values of the original planner's chosen action.
Choose the highest scalar utility among those eligible questions; retain the
original width and action on ties. The continuation still assumes fixed survivor
ordering, so this is a model constraint, not a live-system guarantee. The family
size becomes seven including the unused combination slot. No confirmation has
been generated or consumed.

## Integrated candidate and frozen validation protocol

The vector candidate passed all four consumed official suites with unchanged HR
and MRR and fewer turns. Public and weighted-development score bounds are
positive at alpha .05/7; the small uniform/category changes are not separately
significant. Integrate it behind explicit fusion and exposure policy constants,
with distinct trace status from the original Pareto policy. Cache up to 8,192
immutable reply predictions inside the new planner to limit added computation.
This changes calculation reuse only. The integrated public response digest
matches the research prototype. All 409 tests pass after updating the intended
adapter policy contract and adding question/observation-boundary coverage.

The final validator checks three alternating process pairs on public, weighted,
uniform, category and language development. Every suite must preserve aggregate
HR/MRR/turn efficiency; public and weighted must also have positive adjusted
score bounds. Language must retain complete responses. Require median total
runtime and p95 not to increase on every suite; claim a speed gain only where
the paired saving bound is positive.

Fresh data is generated once with seed 202609085: 1,600 uniform official targets,
1,600 square-root-review-weighted official targets and 800 category-balanced
language targets. All 4,000 targets exclude the preceding 8,200, and are mutually
disjoint. Candidate and wording are frozen before evaluating them. Require
aggregate non-regression on every fresh suite, positive corrected score gain on
the weighted suite, identical language responses, and the same timing gates.
Uniform-only gains will not be claimed significant unless their bound supports
that statement. No changes follow opening confirmation; failure means rejection.

## Runtime v1 rejection and exact reuse v2

The first integrated version passes public accuracy/timing, but weighted median
total runtime is 1.34% slower. Stop validation there; confirmation remains
unopened. Preserve `validation-development/` in full.

Before another timing study, replace the planner-private prediction cache with
one shared by the existing and new planners in `protocol.remaining_reply`.
Its 8,192-entry key contains only bounded ordered card values, normalized allowed
attribute and relevant disclosed values. Titles and unrelated disclosure strings
cannot change a prediction and are omitted. All original argument checks and
the boundary/unknown-attribute ordering precede the cache. Preserve duplicate
card values, exact reply text and candidate observation semantics.

This is an exact calculation-reuse change, not another accuracy hypothesis.
Re-run all development timing gates as `--iteration v2`, keeping v1 artifacts.
Only a passing v2 may evaluate the existing reserved confirmation targets.

## Timing quality audit during v2

During an interruption, weighted baseline elapsed times ranged from 58.17 to
98.76 seconds, whereas candidate times ranged from 58.60 to 60.34 seconds.
The declared median gate passes, but asymmetric external load may explain that
apparent speed gain. Keep every measurement and do not claim a clean 21% speedup.
After the active timing study, run an additional three-pair weighted check using
OS-reported user+system CPU time as well as elapsed time, without changing code
or instrumentation. This is an added measurement-quality check before opening
confirmation, not removal of inconvenient samples or a change to accuracy gates.

## V2 result and user-directed accuracy-first phase

V2 fails uniform timing: median total speedup .982684, about 1.76% slower.
It is not promoted. Confirmation remains unopened. Profiling identifies extra
question branching and hybrid retrieval discarded by the cold-prior policy.
V3 tests an exact question-utility upper bound and defers retrieval on the exact
category-only first turn, leaving later retrieval cache entries uncreated.
These are semantic-preserving runtime hypotheses, to be checked against all
consumed official responses before any performance claim.

The user now explicitly prioritizes accuracy before runtime optimization.
Runtime measurements remain reported, but are deferred as an optimization stage
instead of preventing fresh accuracy validation. HR, MRR and turn efficiency
still must each not regress on frozen suites. No hidden-data guarantees follow.

Before measuring further accuracy candidates, declare two joint-action arms:
`joint_uniform` and `joint_dual`. Starting from the integrated cold/vector
candidate, jointly select a rank-one product and a question on complete support
of at most 200, only when the baseline already displays one product and the
protocol is unlocked. Consider every supported product, preserving all other
relative order. Forecast the same finite fixed-order continuation as the vector
candidate. The uniform arm requires each uniform modeled metric to be no worse;
the dual arm also requires each metric under square-root(1+review-count) weights
to be no worse. Maximize uniform utility, breaking ties with weighted utility,
then preserve the baseline action. No coefficient fitting or target IDs.

This tests whether selecting the product and question together can reduce
ambiguity, where changing the prior alone failed. It is a model assumption, not
an actual-system dominance proof. Family size becomes nine, retaining every
previous arm and the unused combination slot. Screen on the same five consumed
suites, select only from accuracy survivors, then freeze one candidate before
opening the existing 4,000 confirmation targets. Runtime optimization follows
accuracy.

## Joint-model failures and actual-policy verification

Both joint arms improve public MRR/turns but lose uniform turn efficiency; dual
also slightly loses uniform aggregate score. Retain both failures. Their fixed
survivor-order model can disagree with subsequent hybrid retrieval.

Declare `joint_verified` before measuring it (family size ten). Use the dual
joint arm only to propose an action. For a changed proposal, simulate baseline
and proposal continuations through the real, unchanged cold/vector service for
all compatible catalog hypotheses, branching only on visible replies. Preserve
and isolate session/slate/refutation/cache state; use shared read-only retrieval
assets. Require all three predicted metrics under both uniform and square-root
review weights to be non-decreasing, with positive utility in at least one model.
Adopt the proposal's actual current-turn state only if verified; otherwise retain
the baseline action/state. Future hypothetical turns never enter real memory.

This removes the fixed-order continuation assumption from the final acceptance
check, but still assumes the recognized deterministic protocol and declared
priors. Empirical and fresh validation remain necessary. No target label, sample
identity, known test score or private data is available to this controller.
Runtime is measured as a cost to optimize after accuracy screening, following
the user's latest priority. Do not tune after the reserved confirmation is opened.

The first rollout screen is invalid: 12 proposal-execution exceptions and a
copied diagnostics mapping prevented a clean measurement. The 40-row diagnostic
confirms a proposal-execution mismatch. Fix state-copy diagnostics isolation and
preserve `None` questions when the live policy is enumerating exhausted support;
unexecutable proposals retain the baseline response/state and are counted.
Keep these failed implementation runs, and re-screen the corrected hypothesis.
No failed run is used as accuracy evidence or a promotion result.

## Prior-only ties after corrected verification

Corrected actual-policy verification reaches perfect public HR/MRR, but uniform
800 still needs three extra total turns (score .956151 versus .956218), despite
unchanged HR and slightly better MRR. Most proposals are accepted, including
ones whose uniform expected outcome ties the baseline and whose benefit is only
under the popularity prior. Empirical outcomes can move either way on such ties.

Declare `joint_verified_gain` (family size eleven): retain the same proposal and
actual-policy verification, but also require strictly positive uniform expected
utility gain. Retain every component constraint under both priors. This is a
prior-robust acceptance refinement, not a sample-ID exception, threshold sweep
or claim of guaranteed empirical dominance. Freeze and screen it separately;
keep the previous candidate and its failures. No confirmation has been opened.

At the expanded family size eleven, the earlier cold/vector weighted confidence
bound is mathematically zero, with a floating-point residue around 4e-19. Fix the
comparator to normalize bounds within its existing 1e-12 metric resolution to
zero; such a result cannot certify a positive gain. Preserve historical
comparisons and recompute the final family-wide summary. The earlier .05/7
positive bound is a historical development finding, not a current .05/11 claim.

## Close exploration and specify accuracy-first selection before confirmation

Stop adding accuracy hypotheses after the eleven declared slots. Select among
variants that preserve aggregate HR, MRR and turn efficiency on each of the five
consumed suites, with no errors and unchanged language behavior. Among survivors,
choose the highest mean official score across the three non-public development
suites. Public score improvement must have a positive family-eleven bound.

This deliberately revises the earlier *additional* development requirement for
a significant weighted gain: the cold/vector weighted bound becomes zero after
correcting all eleven hypotheses, so that development gain is not established.
It may be selected for a new test, but must not be described as having passed
that earlier gate or as a proven weighted improvement. This is an adaptive
selection change on already consumed data, disclosed before any reserved outcome
is opened. The user's accuracy-first priority removes the runtime blocker;
aggregate accuracy non-regression remains required on every consumed suite.

The reserved confirmation gate is unchanged: freeze one complete implementation
and wording, evaluate the existing uniform 1,600, weighted 1,600 and language 800
once, require component non-regression on each and identical language responses,
and require a positive corrected weighted score-gain bound at alpha .05/11.
Report every suite and all failed earlier candidates. Do not tune on these
outcomes or test another selected accuracy candidate on them if the first fails.
A development winner is a candidate for validation, not an accepted improvement.
Runtime optimization follows a passing accuracy result.

## One terminal replication of the unchanged candidate

The original confirmation stops at its weighted gate. Uniform 1,600 improves
MRR and turns without losing hits. Weighted 1,600 also improves MRR and turns
without losing hits (score .963171 → .963564), but its .05/11 lower bound is
-.00003125. Its predeclared significance gate fails. The language 800 remains
unopened. No runtime or accuracy-policy change is made in response.

Before generating or evaluating additional outcomes, predeclare one larger,
terminal replication of **the same frozen candidate**, source fingerprint
65b6693b3a199910520788250e28fbd4266e5f96e9eb8ddffbeb55dbb00756e3.
Use 6,400 new square-root-review-weighted targets, seed 202609086, excluding all
12,200 earlier or reserved targets. Retain the exact 40/40/15/5 scenario mix and
independent profile sampling. Four times the original weighted sample size
reduces sampling uncertainty for this small effect; no seed/size sweep is allowed.
Use the existing still-unopened language 800 for response-equivalence checking.

The new weighted cohort must preserve each aggregate metric and have a positive
paired-bootstrap score bound at alpha .05/22, a stricter level for this second
look. The sum of the two primary test levels is below .007; only one unchanged
candidate receives these independent tests. The original failed result remains
reported. Do not pool it into the new primary test or relabel it as a pass.
Require zero errors and identical language responses. This is an independent
replication after an inconclusive significance result, not tuning on the first
confirmation. The new driver refuses real metric regressions in the first study,
checks unchanged source/data identities, and refuses overwrites. If this terminal
replication fails, reject the candidate; no further accuracy looks in this round.

## Runtime protocol if the terminal accuracy test passes

Only a passing terminal replication may begin runtime acceptance. Keep the
candidate source unchanged. Cover all nine accuracy-suite instances: five
consumed development suites, original fresh uniform/weighted, new weighted
replication, and reserved language. Retain **every** existing B/C accuracy pair
as repetition one, then add isolated C/B and B/C pairs. This avoids discarding
measurements or selecting a favorable first run. The development public and
weighted reference pairs overlapped earlier research; disclose that limitation.
No competitor or other benchmark runs alongside the two new timing repetitions.

Require each repeated baseline and candidate to reproduce its own validated
sessions and complete response digest. Compare median startup-plus-evaluation
time and p95 across all three pairs, with non-increase on every suite. Capture
OS user+system CPU time in both new pairs and require its median not to increase
as an additional check; there is no fabricated CPU measurement for the first
pair. Claim a speed gain only with a positive paired session-saving bound at
alpha .05/9. Every pair is retained. The runtime driver checks prior accuracy
acceptance, all source/data identities and its own frozen hash, and refuses to
overwrite or continue past a failed suite. It does not reopen accuracy selection.

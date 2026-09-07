# Round 3 — direct exact belief and aggregate acceptance

Declared before round-three measurements, 7 September 2026. Baseline is the
unchanged finalist runtime in commit 5e59d21. The user explicitly replaced the
individual-session veto with aggregate non-regression, statistically supported
gains and fresh validation. Historical round-one/two results retain their
original acceptance rules.

Three independent research arms, no fitting or parameter sweep:

1. `direct_prior`: complete exact transcript support directly drives ranking
   and exposure. Catalog review count breaks observational ties. Bypass bounded
   retrieval and redundant lexical evidence reranking; cache immutable category
   evidence. Keep existing Pareto question planner and enumeration policy.
2. `direct_value`: same path, choosing a question by full-support next-turn
   answer value. Preserve rank-one probing and exhausted-support enumeration.
3. `direct_opportunity`: jointly select a rank-one probe and question using
   marginal continuation value. A probe can rescue a candidate in an ambiguous
   branch while a question identifies others. Use catalog-generated replies,
   a fixed continuation policy and bounded complete support. No target labels.

All arms retain the baseline for unsupported dialogue, unavailable evidence,
zero exact support or invalid requests. Pending override recommendations are
never refuted. Initial ambiguous/boundary openings retain the existing question
lock. Cache entries contain catalog evidence only, never session labels.

Development: previously consumed 800; public 200 is diagnostic. Inspect HR, MRR,
MTTC, score, contract failures and paired session differences. No aggregate HR,
MRR or turn-efficiency loss on any frozen suite. Require a positive multiplicity
adjusted one-sided paired-bootstrap score bound (20,000 draws, alpha .05/3)
on development. Scenario slices diagnose trade-offs; individual losses are
reported but are no longer an automatic veto.

Only a fixed candidate passing development, public aggregate non-regression,
and the frozen language-stress suite may open the unused 1,600 confirmation
sessions. Confirmation uses alpha .05 with no further tuning; failure consumes
the holdout and bars promotion on that evidence. Runtime comparisons run
sequentially in fresh processes, require no median evaluation/p95/startup
regression over three alternating paired runs, and report variability. A code
revision after confirmation requires new untouched validation before promotion.

Promotion means changing the personal fork only. The team checkout and upstream
remain unchanged. No finite evaluation can guarantee winning or a hidden .99.

## Follow-up after the three declared screens

All three initial arms fail aggregate development non-regression. The direct
path is substantially faster, but changing the prior remains unjustified.
`baseline_continuation` therefore keeps baseline retrieval/ranking and the
rank-one probe, selecting a question by full-horizon fixed-order continuation
value. Its screening bound accounts for four hypotheses (.05/4).

Separately, profile and test a behavior-preserving runtime optimization. Its
primary endpoint is runtime, not score: require identical response digests and
per-session results on development, public, stress and fresh confirmation;
paired latency improvement with a positive bootstrap lower bound, plus no
median startup/p95/whole-suite runtime loss over three alternating pairs.
This may be accepted as an efficiency improvement, never described as an
accuracy gain. The untouched confirmation suite is opened only after its
development/public/stress checks pass. This distinct acceptance path is
declared before selecting or measuring a runtime optimization.

Before the final repeated timing run, define aggregate runtime operationally
as **cold start plus complete evaluation**, with p95 response latency as the
tail safeguard. Report cold start separately; the cache changes post-start
computation and should not be selected for an accidental startup fluctuation.
This replaces the separate startup-median veto above, while retaining cold
start in every end-to-end comparison. All runs, including slower measurements,
remain in the report. Use three alternating pairs on each suite. For the three
development suites use bootstrap alpha .05/3; fresh confirmation uses .05.

## Second runtime candidate, before measurement

The first complete timing study passes development and public, but stress has
a 0.09% slower median total time and a 1.24% higher p95. It fails the literal
runtime gate; do not open confirmation. Retain every v1 timing output.

The profiler also identified repeated pure Stage-A tokenization. Add a bounded
512-entry cache for inputs up to 4,096 characters, with longer text using the
original calculation. It preserves Unicode normalization, token order and
duplicates. This targets the ordinary fallback path as well as exact dialogue.

The category query additionally uses binary equality while the existing index
is NOCASE. Add a redundant NOCASE equality to permit use of that index, retaining
the original binary equality so case-distinct categories remain separate. Test
both result equivalence and the query plan. No new index or ranking rule.

Freeze v2 after tests and repeat the same three paired runs on development,
public and stress. For this second runtime hypothesis use .05/6 on development
and public timing confidence bounds (two candidates, three suites); stress
requires non-regression, not an independent speed-gain claim. Only a clean pass
opens the untouched 1,600. Confirmation remains .05 with no subsequent tuning.

## Fixed competitor comparison after runtime confirmation

After the sequential timing study finishes, also evaluate the three previously
reviewed, source-accessible competitor snapshots on the same 1,600. Use their
unchanged, pinned source and the same official evaluator/catalog; keep optional
network/model features disabled as in round one. This does not select or tune
our frozen candidate. Report paired score bounds with alpha .05/3 and each
aggregate metric. Their timings are not part of our non-regression gate.
ARC/Fable7 remain untestable without accessible source; do not convert their
reported scores on different samples into controlled wins or losses.

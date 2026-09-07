# Reproduce the finalist review

For the latest aggregate gate and runtime study, see the round-four section
at the end of this document. The original rounds below are retained as history.

Run from the personal checkout after following its normal runtime setup. The
measurement environment was Python 3.13.15, macOS arm64, using the pinned runtime
requirements and the bundled BGE assets. Experiments are invoked explicitly;
`python -m evaluator.local_evaluator` still runs the unchanged submission Agent.

## Baseline and tests

```bash
python -m unittest discover -s tests
mkdir -p benchmarks/finals-review
python -m scripts.benchmark_finalists \
  --dataset data/public_set.jsonl \
  --output benchmarks/finals-review/public-baseline.json
```

Observed public result: HR@10 1.0, MRR 0.99625, MTTC 2.35, TechnicalScore
0.971875, zero model tokens, exceptions or invalid outputs. The sequential
instrumented run took 4.19 seconds to initialize and 17.27 seconds to evaluate
470 responses; mean response 36.63 ms, p95 78.45 ms, max 182.45 ms. These are
local observations, not CPU limits or a claim about the judges' hardware.

## Regenerate the frozen data

```bash
python -m scripts.generate_target_disjoint_suite \
  --count 2400 --seed 202609071 \
  --output benchmarks/finals-review/frozen-2400.jsonl
python - <<'PY'
from pathlib import Path
root = Path('benchmarks/finals-review')
rows = (root / 'frozen-2400.jsonl').read_text().splitlines(True)
(root / 'development.jsonl').write_text(''.join(rows[:800]))
(root / 'confirmation.jsonl').write_text(''.join(rows[800:]))
(root / 'language-stress.jsonl').write_text(''.join(rows[:200]))
PY
```

Hashes are in the experiment plan and results manifest. Development contains
327 Buying, 322 Browsing, 111 Override and 40 Boundary sessions. Language stress
contains 81/82/25/12 respectively. "Fresh" means a newly sampled suite for this
review, with public targets excluded. Historical synthetic target lists are not
fully available, so non-overlap with every prior synthetic experiment is not
claimed. The 800 and 1,600 partitions are disjoint from each other.

The profiles are sampled from safe aggregate public profiles, independently of
the newly chosen targets. This tests mechanics, not profile/target calibration.
No upstream purchase records or hidden labels are reconstructed.

## Local experimental arms

```bash
python -m scripts.benchmark_finalists \
  --dataset benchmarks/finals-review/development.jsonl \
  --output benchmarks/finals-review/development-baseline.json
python -m scripts.benchmark_finalists \
  --arm strict_top1 --dataset benchmarks/finals-review/development.jsonl \
  --output benchmarks/finals-review/development-strict-top1.json
python -m scripts.compare_finalist_results \
  benchmarks/finals-review/development-baseline.json \
  benchmarks/finals-review/development-strict-top1.json \
  --output benchmarks/finals-review/strict-top1-comparison.json
```

Other explicit arms: `cold_start_reviews`, `lossless_slots`, and exploratory
`catalog_category`. Add `--wording paraphrase` with `language-stress.jsonl` to
test the fixed envelope changes. Do not repeatedly tune against those 200 rows;
the suite was consumed for development in this review.

The runner preserves detailed session outcomes in ignored local output files;
committed `results-summary.json` and paired reports contain aggregate results,
hashes, source identities and no target ASINs or transcripts.

## Competitor reproduction

Obtain the source at the following reviewed commits. Do not install optional
models or run downloaded shell scripts. The core implementations reviewed here
use the standard library. No code from these repositories is bundled in ours.

| Repository | Commit | Import root | Module |
|---|---|---|---|
| [Kopi](https://github.com/shaohong126/techjam-Kopi-O-1-) | `ddd5b30cdff74fd422fcf30a1f16d020732f809d` | Repository root | `starter.agent` |
| [Vibe](https://github.com/Panecord/Tiktok-TechJam---AI-shopping-assistant) | `0af6251ae2d747a299057fe521358b4b9fc0c9e3` | `techjam-conversational-search` | `starter.agent` |
| [Shreyansh](https://github.com/13shreyansh/shopping-copilot-techjam-2026) | `a56991a5116ff7c1868fc67ea19f4d6496f12615` | Repository root | `submission.agent` |

```bash
python -m scripts.benchmark_finalists \
  --external-root /path/to/reviewed/kopi \
  --module starter.agent \
  --dataset benchmarks/finals-review/development.jsonl \
  --output benchmarks/finals-review/development-kopi.json
```

The runner imports our unchanged official evaluator first, then loads the
explicitly selected competitor in a fresh process. It removes `COPILOT_*`
environment variables from that process to keep Vibe's documented offline
default. Raw credentials are never read or printed. This is configuration
isolation, not a sandbox for arbitrary unreviewed code.

Development jobs overlapped, so their timings are not a fair comparative speed
benchmark. The final baseline timing and the supplemental competitor language
runs were sequential. The official evaluator has no per-response timeout in
this released source; the runner records latency rather than silently changing
the contract.

## Artifact integrity and adoption

The evaluator and public data copied into the accessible Kopi and Vibe projects
are byte-identical to ours. Every runtime uses our catalog, whose SHA-256 is
`da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67`.
The official evaluator hash is
`79a5ea06f9a1b8c5036f30efa85dc1f36b8f6b06eb8feb8f545dfa767bc45564`.

At the end of the initial review, no candidate cleared its non-regression gate;
the confirmation partition was then unused. It was subsequently consumed in
round three. There is no team PR to merge from this review. If reviewing the branch
against team `main`, distinguish the first baseline-snapshot commit (pre-existing
local work) from the subsequent review/tooling commit.

## Round three: aggregate decisions and response-identical runtime

The user's revised accuracy gate is explicit:

```bash
python -m scripts.compare_finalist_results baseline.json candidate.json \
  --gate aggregate --family-size 4 --output comparison.json
```

It checks aggregate HR, MRR and turn efficiency separately and retains the
paired score confidence requirement. Individual losses remain visible but no
longer automatically veto promotion. Omit `--gate` to reproduce the historical
pointwise gate. The four new research arms are `direct_prior`, `direct_value`,
`direct_opportunity` and `baseline_continuation`; none is selected by the
submission entry point.

For response-identical runtime comparisons, create a separate baseline source
archive at `5e59d21` using `git archive`. Copy the **current**
`scripts/benchmark_finalists.py` into that archive so both trees use identical
instrumentation. Supply its ignored `data/catalog.jsonl` from the same frozen
catalog; model assets are already tracked in the archive. Do not use an external
module import that could accidentally retain the candidate's Python modules.

```bash
python -m scripts.benchmark_runtime_pairs \
  --baseline-root /absolute/path/to/baseline-runtime \
  --candidate-root /absolute/path/to/personal-checkout \
  --data-root /absolute/path/to/frozen-suites \
  --output /absolute/path/to/new-timing-output \
  --runtime-family-size 2
```

This runs three sequential alternating pairs on development, public and stress.
It refuses to overwrite any repetition. The runner records exact response
digests, per-session timings, source/data/evaluator identities, exceptions,
invalid output and peak process RSS. Raw files stay local; aggregate reports
contain no session transcripts or target IDs.

Only after those gates pass, run the same command with `--confirmation` and a
new output directory to evaluate the reserved 1,600, without changing the agent.
That partition is consumed once opened; it cannot serve as a fresh holdout for
later tuned policies. Use [ROUND3-RESULTS.md](ROUND3-RESULTS.md) for its actual
status and the observed results, including the rejected first runtime candidate.

## Round four: frozen language repair and exact pruning

Use a **new research directory** with the original generated `development.jsonl`,
`confirmation.jsonl` and `language-stress.jsonl` from above. Reproducing a consumed
suite verifies a result; it does not make that suite fresh for another experiment.
Keep the original outputs intact. The following paths are illustrative absolute
paths and should be replaced with your new research root and personal checkout.

```bash
python -m scripts.generate_distribution_suites \
  --exclude /absolute/research/development.jsonl \
  --exclude /absolute/research/confirmation.jsonl \
  --seed 202609074 --output /absolute/research/round4/suites
```

The generator excludes public targets automatically. It produces two development
suites (weighted/category, 800 each) and three confirmation suites (uniform 1,600,
weighted 1,600, category 800), mutually target-disjoint. Compare their hashes with
the committed `round4-results-summary.json`. Weighted means sampling without
replacement using square-root review counts; category means uniform choice of a
remaining coarse category followed by a product in it. These are sensitivity
populations, not estimates of the private target distribution.

Create `/absolute/research/round4/baseline` from `git archive 1ef7440`, and supply
its ignored catalog from the same frozen catalog. Copy the **current**
`scripts/benchmark_finalists.py` into that archive so both sides use identical
instrumentation and wording transforms. Keep model assets from the archive.
Then run from the personal checkout:

```bash
python -m scripts.validate_planner_pruning \
  --reference /absolute/research/round4/baseline/conversational_search/exposure.py \
  --output /absolute/research/round4/pruning-differential.json
python -m unittest discover -s tests
python -m scripts.validate_finals_round4 \
  --research-root /absolute/research \
  --candidate-root /absolute/personal-checkout --stage development
python -m scripts.validate_finals_round4 \
  --research-root /absolute/research \
  --candidate-root /absolute/personal-checkout --stage confirmation
```

The validator refuses existing output directories and requires every development
gate plus an unchanged source fingerprint before confirmation. Every suite runs
three sequential process pairs in B/C, C/B, B/C order. Official wording requires
identical session outcomes and complete response digests. Changed language
requires non-decreasing aggregate HR/MRR/turn efficiency and a positive paired
score-gain bound at alpha .05/8 (seven ranking hypotheses plus one language
intervention). An official identical-accuracy arm deliberately does not pass
the separate strict-score-improvement comparator; its adoption route is identical
behavior plus measured runtime improvement.

Both routes require non-increasing median total runtime and p95, and a positive
session-block timing saving bound. Timing alpha is .05 divided by the number of
suites in that stage. Both bootstrap procedures use 20,000 draws. Whole response
and session identities are checked independently from rounded metric summaries.

The separate explicit research arms are `support_cold_prior`, `first_turn_prior`,
`soft_prior`, `recoverable_prior`, `ambiguous_probe`, `cold_ambiguous` and
`dominant_prior`. All are rejected and none is enabled by the Agent entry point.
Screening of those arms preceded the final intent repair; reproduce their exact
historical source from the recorded runtime fingerprints/baseline when comparing
changed-language inputs. Official responses of the baseline and accepted repair
were identical on the screened official suites.

After the primary timing study, a single replay of the old round-three
confirmation checks preservation of its responses. It is explicitly a consumed
suite replay and is not included in the fresh 4,000-target claim.

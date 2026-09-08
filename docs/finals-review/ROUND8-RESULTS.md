# Round eight: bounded conversation fixes

**Decision: adopt the bounded correction fixes in the personal fork.** All
four end-to-end accuracy/compatibility gates pass. The independent language
challenge shows no general-language improvement. No runtime changes were made
after confirmation began. Runtime measurements are recorded below.

Baseline: `749f695ac302f639147729550eab1d2576e43591`.
Source fingerprint:
`e2ad2c8a126270cdd916151703e1456847d2319523cb5910c0de88c0a587f4b7`.
See the [predeclared plan](ROUND8-PLAN.md) and
[competition-first scope map](COMPETITION-FIRST-PRIORITIES.md).

## Changes and actual scope

The candidate fixes explicit preference edits followed by “keep everything
else,” polite exclusion punctuation, ambiguous singular references to several
earlier preferences, and loss of explicit importance during normalization.
A finite apparel grammar can also split a completely recognized single-sentence
opening into category, color, material and maximum budget. Unknown modifiers,
multiple possible nouns, alternatives and incomplete interpretations fall back
without a partial interpretation. That fallback itself is not a successful
understanding of the request.

For example, the development case `I need a blue cotton T-shirt under $50`
previously became a single category string with no independent requirements.
It now produces category `T-shirt`, color `blue`, material `cotton` and budget
`under $50`. `Change the color to black; keep everything else` retains the
original material and budget. These examples were used during development and
are not held-out evidence.

Normal search retains the same BM25/BGE retrieval, exact comparator, protocol
recognition, Pareto planning and profile policy. New parsing does not create
simulator events or authorize continuation refutation. The round-seven attribute
index is still not loaded by the active adapter. Empty or fallback searches use
truthful response wording while preserving selected IDs and question decisions.

## End-to-end accuracy

The 1,200 new targets exclude all 22,600 prior/reserved targets and are mutually
disjoint. Seed `202609089`; 400 official-wording targets are uniform, and 800
language targets use square-root-review weighting. Profiles are independently
sampled. Scenario proportions are 40/40/15/5 for buying/browsing/override/boundary.
The original evaluator controls disclosure, stopping and exact-ASIN scoring.

| Evaluation | HR before → after | MRR before → after | Mean turns before → after | Score before → after |
|---|---|---|---|---|
| Public 200 | 1.000000 → 1.000000 | .996250 → .996250 | 2.35000 → 2.35000 | .971875 → .971875 |
| Fresh official 400 | .995000 → .995000 | .988357 → .988357 | 2.57750 → 2.57750 | .962457 → .962457 |
| Fresh language 800 | .830000 → .938750 | .756459 → .843118 | 3.74625 → 2.96000 | .787013 → .883110 |
| Consumed language 800, compatibility only | .907500 → .907500 | .630714 → .630714 | 3.17625 → 3.17625 | .799439 → .799439 |

Public, fresh official and consumed compatibility responses match completely.
There are zero exceptions or invalid outputs in every run. The language score gain
is .096097768; the one-sided paired bootstrap lower bound is .074178547, using
20,000 draws at alpha .05/4. All three aggregate accuracy components improve.
There are 90 improved, 11 regressed and 699 unchanged sessions, with 89 gained
hits and two lost hits. This meets an aggregate rule, not every-session dominance.

**All measured score improvement is in intent-override sessions.** Buying,
browsing and boundary mean scores are unchanged. The declared wording adds
`keep everything else` to explicit overrides and moves simple color/material
clues before category nouns. These are development-derived sentence families;
fresh target sampling does not turn them into independent natural language.
Component attribution is reported separately below.

## What caused the measured improvement

After confirmation, two ablations removed components one at a time on the now
consumed language targets. They are explanatory comparisons, not fresh
validation or a search for a different deployment candidate.

| Configuration | HR | MRR | Mean turns | Score |
|---|---:|---:|---:|---:|
| Frozen candidate | .938750 | .843118 | 2.96000 | .883110 |
| Without composed opening parser | .938750 | .843118 | 2.96000 | .883110 |
| With previous prose-operation reducer | .830000 | .756459 | 3.74625 | .787013 |

Removing the opening parser preserves the candidate's complete responses;
restoring the previous prose-operation reducer restores the baseline's session
outcomes. The measured gain is attributable to the operation repair under these
wording conditions. **The new opening parser has no demonstrated additional
benchmark benefit.** Its value is limited to the explicit development examples
and unit-tested grammar; it has not generalized to the independent corpus.
Neither adding embeddings nor an attribute index produced this gain.
See [ablation measurements](round8-ablation-summary.json).

## Independent language challenge: no improvement

A separate agent authored 52 conversations and their semantic expectations
without reading the implementation or tests. Implementers did not inspect the
corpus until source was frozen. It covers more varied wording, compounds,
currencies, requirements/preferences, retractions, negation and references, and
includes products beyond the frozen apparel catalog. All cases are retained;
none is excluded after seeing the outcome.

**Both versions score 0/52 on complete structured-intent correctness. Their
final states and all 85 per-turn states are identical.** Preserving a sentence as an untyped soft clue does
not count as extracting the requested category, constraints and importance.
This is a state-interpretation check, not an end-to-end shopping success rate.
The corpus is model-authored and model-adjudicated, not an independent human
study or a representative random shopper sample.

The result rules out a claim that this candidate solves broad language
understanding. The new grammar still misses compound color names, many budget
forms, multi-sentence composition, indirect edits and reference resolution.
Adding another few rules cannot be presented as a validated semantic parser.
No fixes were tuned on this corpus after it was opened.

The [full all-case adjudication](round8-language-review/intent-adjudication.md)
includes frozen expectations, both sets of states, collection code and the
model's recorded findings. All 52 failures are disclosed. Initial extraction
failures mask many intended edit tests; the corpus cannot establish which
version handles already-typed edit contexts better.

## Runtime and validation

All **457 unit tests pass**. Three sequential public-suite timing pairs alternated
execution order after all accuracy and ablation jobs finished. All six timing
runs preserve complete responses. Median measurements are:

| Measurement | Before | After |
|---|---:|---:|
| Startup plus evaluation | 17.1362 s | 17.0491 s |
| Mean response latency | 27.9433 ms | 27.8651 ms |
| p95 response latency | 52.2316 ms | 51.7913 ms |
| Process peak RSS | 657.9375 MiB | 661.4844 MiB |

These point estimates meet the aggregate runtime non-regression check but do
**not** establish a speedup. The mean paired per-session saving is -.12596 ms and
its one-sided lower bound is -.21434 ms. Median whole-run and per-session paired
summaries can differ; neither should be hidden. Peak memory rises about 3.55 MiB.
Adoption follows accuracy-first prioritization. Timing applies to the public
wording path, not a claim of measured latency for all natural conversations.
See [timing measurements](round8-runtime-summary.json) and
[accuracy evidence](round8-results-summary.json).

## Architecture before and after

| Layer | Before | Candidate |
|---|---|---|
| Initial request | Some attribute-bearing openings become an opaque category | Split only fully recognized apparel openings into independent slots |
| Preference edits | Retain-other wording can invalidate an otherwise explicit edit | Validated edits accept a bounded retain-other clause |
| Ambiguous withdrawal | Singular earlier-preference reference can remove several initial slots | Preserve old requirements when the reference is ambiguous |
| Importance | Some normalization removes the cue | Preserve explicit need/prefer/should and mandatory price ceilings |
| Failure response | May call fallback products closest matches | Identify fallback options and empty results |
| Retrieval, evidence ranking, questions, models | Accepted round-six policies | Unchanged policies |

The measured improvement is bounded conversational correctness under the tested
forms. It does not establish hidden-800 accuracy, superiority over a competitor,
human decision quality or improved conversion.

## Reproduction and repository boundary

The personal fork retains the frozen runtime, tests, independent intent corpus,
both sets of intent states, model adjudication, aggregate results and runners.
Large raw end-to-end results, target suites, baseline archive and timing runs
remain in local ignored `../round8` research storage. They are needed to replay
the exact end-to-end comparisons; the aggregate bundle alone is not a complete
portable dataset. Neither the team repository nor the organizer evaluator was
modified.

With those frozen local inputs in a separate output checkout (the validation
drivers refuse to overwrite existing result directories):

```
python -m unittest discover -s tests
python -m scripts.validate_composed_requests
python -m scripts.measure_composed_runtime
```

`scripts/ablate_composed_requests.py --without openings|operations` uses the
same source-root, catalog, dataset and output arguments as the language runner.
It only performs the documented process-local explanatory ablation. Runtime
source was not edited after the freeze. All opened targets and language cases
are now consumed evidence for subsequent work.

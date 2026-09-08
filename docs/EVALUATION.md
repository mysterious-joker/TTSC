# Evaluation evidence

> **Finals update (8 September 2026):** the active bounded-prior champion
> controller supersedes the historical tables below. On the unchanged public
> evaluator it reaches HR@10 `1.000`, MRR `1.000`, MTTC `2.000`, and
> TechnicalScore `0.980000`. See the
> [final report](finals-review/ROUND11-CHAMPION-SOLUTION.md) for the frozen
> purchase-derived confirmation and disclosed uniform sensitivity result.

## Reproducible public result

The active `starter.agent.Agent` was run with the unmodified organizer
evaluator on 1 September 2026:

```bash
.venv-runtime/bin/python -m evaluator.local_evaluator
```

| Scenario | N | Hit Rate@10 | MRR | MTTC |
| --- | ---: | ---: | ---: | ---: |
| Buying | 80 | 1.000 | 0.990625 | 1.9000 |
| Browsing | 80 | 1.000 | 1.000000 | 2.2125 |
| Intent Override | 30 | 1.000 | 1.000000 | 3.8000 |
| Boundary | 10 | 1.000 | 1.000000 | 2.7000 |
| **Overall** | **200** | **1.000** | **0.996250** | **2.350** |

```text
Efficiency      0.8650
TechnicalScore  0.971875
Prompt tokens   0
Completion      0
```

The active submission is fully deterministic and does not initialize or call
an LLM. The reported prompt and completion token counts are therefore zero.

The original organizer BM25 starter reported Hit Rate@10 `0.125`, MRR
`0.068034`, MTTC `9.81`, and TechnicalScore `0.106710`.

## Protocol-posterior and metric-aware promotion

The active protocol layer was developed from the published simulator contract
and frozen catalog cards. The final width planner was derived from the
published scoring equation. No public target labels, target IDs, or per-case
failures enter either algorithm.

Aggregate-only comparisons used one shared retrieval backend. `Posterior`
means exact full-catalog replay, rank-one probing, and eligible continuation
refutation. `Metric-aware` adds the exhausted-posterior dynamic program.

| Frozen suite | Arm | N | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Organizer public | Posterior | 200 | 1.000000 | 0.969583 | 2.260000 | 0.965675 |
| Organizer public | Metric-aware | 200 | 1.000000 | 0.996250 | 2.350000 | 0.971875 |
| Independent buying holdout | Posterior | 384 | 0.994792 | 0.969076 | 1.903646 | 0.970046 |
| Independent buying holdout | Metric-aware | 384 | 0.994792 | 0.987956 | 1.960938 | 0.974564 |
| Mixed target-disjoint stress | Posterior | 800 | 0.931250 | 0.895805 | 2.868750 | 0.896991 |
| Mixed target-disjoint stress | Metric-aware | 800 | 0.931250 | 0.918220 | 2.952500 | 0.902041 |

The final candidate preserved hit rate on all three suites while improving MRR
and TechnicalScore. The mixed suite includes unsupported shifted language;
those turns exercise the ordinary fail-open hybrid path.

## Pareto-safe protocol planning

The active planner adds typed-question lookahead only when it weakly dominates
the prior rank-one/`other` policy for every candidate in the exact posterior.
The planner uses reconstructed frozen-catalog cards, deterministic official
reply partitions, continuation refutation, and the published metric. It has no
target prior, public-case threshold, or fitted parameter.

The comparison suite was frozen at seed `20260901` before evaluation, excluded
all 200 public target ASINs, used the official 40/40/15/5 scenario mix, and let
the unmodified evaluator materialize every hidden card and message.

| Frozen suite | Arm | N | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Organizer public | Metric-aware | 200 | 1.000000 | 0.996250 | 2.350000 | 0.971875 |
| Organizer public | Pareto-safe | 200 | 1.000000 | 0.996250 | 2.350000 | 0.971875 |
| Target-disjoint official templates | Metric-aware | 800 | 0.992500 | 0.981654 | 2.566250 | 0.959421 |
| Target-disjoint official templates | Pareto-safe | 800 | 0.992500 | 0.981654 | 2.566250 | 0.959421 |

A second untouched seed (`20260902`) evaluated the full-catalog strict-
refinement extension. Metric-aware and Pareto-safe policies were again
identical across every aggregate and scenario metric: HR@10 `0.985000`, MRR
`0.973948`, MTTC `2.582500`, and TechnicalScore `0.953034` on 800 cases.

A focused card-level test covers the improvement case absent from those two
aggregate suites: `other` exposes two shared early card values, while a typed
`color` question skips the truncation and separates all remaining candidates.
The Pareto planner selects `color` at the same rank-one width. An earlier
unconstrained width-and-question experiment was rejected: on the same 800-case
suite it changed TechnicalScore from `0.959421` to `0.959215` by trading too
much MRR for a 0.00375-turn MTTC reduction.

## Teammate `yl-dev` reproduction and synthesis check

The unmodified `yl-dev` head at commit `5684ff9` was evaluated against the same
catalog. Its evaluator and public dataset are byte-identical to the official
copies in this repository.

| Agent | Frozen suite | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: |
| `yl-dev` | Organizer public 200 | 0.990000 | 0.948500 | 2.785000 | 0.943850 |
| Active agent | Organizer public 200 | 1.000000 | 0.996250 | 2.350000 | 0.971875 |
| `yl-dev` | Independent buying 384 | 0.971354 | 0.892006 | 2.708333 | 0.919112 |
| Active agent | Independent buying 384 | 0.994792 | 0.987956 | 1.960938 | 0.974564 |

The teammate's mixed shifted-language run was stopped rather than reported as
a score: unsupported messages repeatedly enter `filter_by_constraints`, which
scans all 50,000 cached product texts for each turn. Our bounded fallback
completed the same 800-case suite in about 65 seconds. This is why the adaptive
substring matcher was not transplanted into the runtime path.

The teammate branch's new confidence gate motivated a stricter synthesis test:
retain our official-score dynamic program but replace its uniform
indistinguishable-survivor posterior with the existing harmonic rank prior.
The experiment reached public MRR `1.0` and TechnicalScore `0.972100`, but on a
fresh 400-case target-disjoint official-template subset it reduced
TechnicalScore from `0.966950` to `0.966325`. It was rejected and removed. This
keeps the useful confidence-sensitive principle without importing its
miscalibrated prior or public-tuned threshold.

## Earlier target-disjoint checks

These are synthetic robustness tests, not organizer-private scores:

| Frozen suite | N | HR@10 | MRR | MTTC | TechnicalScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fresh target-disjoint suite, mixed official/shifted language | 800 | 0.965 | 0.774515 | 2.53625 | 0.884130 |
| Earlier clean-room hidden-generalization suite | 800 | 0.845 | 0.622242 | 3.6875 | 0.755423 |

Both suites excluded previously used target products and contained the official
40% Buying, 40% Browsing, 15% Intent Override, and 5% Boundary mix. The score
spread is reported deliberately: template and simulator choices materially
affect local results, so neither suite proves the hidden distribution.

## Rank-safe exposure promotion evidence

The active preview rule was derived from the published stopping rule: a
provisional hit below rank 1 ends the session before clarification can improve
its reciprocal rank. The candidate therefore exposes only rank 1 on a healthy
turn-one category-only state, asks `other`, and otherwise preserves the prior
policy.

Before promotion, the old and candidate policies were compared on the same
fresh deterministic suite of 800 catalog targets. It used seed `20260831`,
excluded every public target, preserved the official 40/40/15/5 scenario mix,
and assigned the released anonymous profiles independently of target choice.
No per-case output was inspected.

| Arm | N | HR@10 | MRR | MTTC | TechnicalScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Buying-top3 policy | 800 | 0.961250 | 0.783774 | 2.493750 | 0.885882 |
| + category-only top1 preview | 800 | 0.961250 | 0.812506 | 2.540000 | 0.893577 |

| Scenario | Baseline MRR | Preview MRR |
| --- | ---: | ---: |
| Buying | 0.814722 | 0.814722 |
| Browsing | 0.733125 | 0.801249 |
| Intent Override | 0.859653 | 0.859653 |
| Boundary | 0.713750 | 0.743403 |

The fresh check preserved HR in every scenario. It confirms the intended
tradeoff—slightly later first hits for materially better ordering—without
relying on public target overlap. It remains synthetic evidence rather than a
private-score estimate.

## Smart-routing promotion evidence

The final routing rule was fixed around catalog support and output-width
invariants, then compared with always-hybrid on frozen target-disjoint targets.
No failed product, target ID, or per-case output was inspected.

| Frozen target-disjoint check | Arm | N | HR@10 | MRR | MTTC | TechnicalScore |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Phase 17 official-template surface | Always hybrid | 400 | 0.9600 | 0.813971 | 2.485000 | 0.894491 |
| Phase 17 official-template surface | Smart hybrid | 400 | 0.9600 | 0.815221 | 2.485000 | 0.894866 |
| Separate Phase 14 buying holdout | Always hybrid | 384 | 0.950521 | 0.838759 | 2.096354 | 0.904961 |
| Separate Phase 14 buying holdout | Smart hybrid | 384 | 0.950521 | 0.841797 | 2.096354 | 0.905873 |

An earlier, broader gate required only one structurally supported BM25 result.
It improved the public score to `0.904726` but reduced the Phase 17
official-template score from `0.894491` to `0.893216` and lost one hit. That
version was rejected. The promoted gate requires at most three jointly exact
candidates and complete BM25 coverage of that set. The independent Phase 14
holdout was run only after this final rule was fixed.

## Last rejected experiments

| Candidate | Frozen comparator | Candidate result | Decision |
| --- | ---: | ---: | --- |
| Importance-aware MUST/SHOULD/PREFER reranker | 0.870921 | 0.852252 | Rejected |
| Dense-term BM25 repair while retaining hybrid fusion | 0.884130 | 0.884130 | Inactive; no measured gain |
| Score-threshold dynamic exposure | 0.884130 | 0.767233 | Rejected |
| Repair plus dynamic exposure | 0.884130 | 0.767233 | Rejected |
| Broad any-support BM25 trigger | 0.894491 | 0.893216 | Rejected on target-disjoint check |
| Dense-only exact-best-tier tie-break | 0.894866 | 0.893160 | Rejected on target-disjoint check |
| Raw-cosine 0.02-margin best-tier tie-break | 0.894866 | 0.894741 | Rejected on target-disjoint check |
| Harmonic rank-prior metric planner | 0.966950 | 0.966325 | Rejected on target-disjoint official-template check |

The active code therefore keeps exact-evidence reranking and conservative smart
hybrid routing, then adds full-catalog protocol replay, eligible continuation
refutation, and metric-aware posterior enumeration.

## Runtime disclosure

The public confirmation diagnostic measured:

| Quantity | Measurement |
| --- | ---: |
| Respond calls | 486 |
| p50 response latency | 23.50 ms |
| p95 response latency | 44.43 ms |
| Maximum response latency | 92.96 ms |
| Evaluation wall time | 11.45 s |
| Process peak RSS | approximately 632 MB |
| Runtime network calls | 0 |
| External model/API calls | 0 |
| Reported tokens | 0 |
| Estimated API cost | USD 0 |

Measurements are machine- and cache-dependent. The model and index occupy
about 107 MiB on disk; the 50,000-row catalog is approximately 58 MiB and is
downloaded separately from the organizer release.

## Reproducibility boundaries

- Only aggregate results are reported here.
- The official public set is development data and influenced system design.
- No claim of 100% non-overfitting or private-set equivalence is made.
- The frozen target-disjoint tests reduce product overlap but still use local
  deterministic simulators.
- Rejected candidates were not activated after observing their outcomes.
- The active entry point is `starter.agent.Agent`; the root `agent.Agent`
  is an exact re-export.

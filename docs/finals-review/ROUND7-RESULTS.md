# Round seven: attribute-index experiment

**Decision: keep the current agent. Neither tested ranking integration passes
the accuracy gate.** The index and experiments are retained as opt-in research;
`starter.agent.Agent` does not import or load them. No response-time promotion
study was run after the accuracy failures, and no speed improvement is claimed.

Baseline: `c3a18924ffbef04e11b377a06f46d19cfb012628` (accepted language repair).
Frozen source fingerprint:
`b9432668fe418394156ef9702a61c5aaab79620955f0fda1f5284938b05ef1db`.
See the [plan and pre-confirmation amendment](ROUND7-PLAN.md) and
[aggregate evidence bundle](round7-results-summary.json).

## What was built

The experimental sidecar stores material, color, size, brand, style and selected
feature observations, including their original field/text source, polarity and
evidence tier. Explicit detail fields provide stronger observations; bounded
title/feature mentions provide weaker observations. Existing category and price
handling are reused. Manufacturer and package dimensions are not treated as
brand or wearable size.

Lookups return match, counterevidence, unknown or conflict. Missing fields and
unlisted parent-product variants remain unknown. Opposing observations produce
conflict and contribute zero. Word boundaries avoid `blueberry` → blue; negation
avoids `cotton-free` → affirmative cotton. Composition tests distinguish 100%
cotton from merely containing cotton. Positive token evidence does not prove
complete semantic satisfaction of every modifier in a shopper's request.

The SQLite sidecar contains indexed bitmaps and provenance rows, bound to the
catalog SHA-256 and schema version. Queries retrieve attribute postings rather
than rescanning descriptions. Missing, stale or corrupt indexes fail open.

| Artifact | Products | Facts | Posting keys | File bytes |
|---|---:|---:|---:|---:|
| Full attribute sidecar | 50,000 | 160,656 | 3,422 | 42,221,568 |
| Detail-field suppression sidecar | 50,000 | 150,879 | 91 | 28,041,216 |

Only 9,777 observations come from explicit fields; 150,879 come from text.
The catalog has explicit Color fields on 2,439 products, Material on 2,069,
and Size on 925. For cotton, the index finds 213 products with affirmative field
evidence and 9,411 with affirmative text mentions. This is sparse structured
coverage, not a complete product-attribute database.

## Two frozen integrations

Both operate only after unsupported wording disables exact protocol consistency,
and only within the existing exact ranker's best evidence tier. They preserve
the candidate set and other tiers, update belief ordering consistently, and do
not introduce hard filtering.

1. **Field-first tie-break:** prefer field evidence, then text evidence, with
   counterevidence subtracting support and stable original rank breaking ties.
2. **Counterevidence-only tie-break:** known positive evidence and unknown both
   contribute zero. Only opposing observations may demote a tied candidate.

The first arm reduced development MRR, so the second was defined before fresh
evaluation to test negation without rewarding metadata completeness. Both were
then frozen. No source changed while confirmation ran, and no thresholds or
product-specific rules were tuned against its results.

## Fresh results

Seed `202609088`. The 800 weighted language targets and 400 category-balanced
suppression targets are disjoint from each other and all 21,400 prior/reserved
targets. Profiles are independent of target choice. Each suite includes
Buying/Browsing/Override/Boundary scenarios in the fixed 40/40/15/5 mix.
Paraphrase transforms are the previously declared round-six transforms, not new
unseen language families. The evaluator and exact-ASIN correctness are unchanged.

**800 fresh targets with attribute-language paraphrases:**

| Agent | HR | MRR | Mean turns | Score |
|---|---:|---:|---:|---:|
| Current baseline | .907500 | .630714 | 3.17625 | **.799439** |
| Field-first index | .907500 | .599522 | 3.18000 | .790007 |
| Counterevidence-only index | .905000 | .627151 | 3.22500 | .796145 |

The first arm has 634 ranking interventions, 72 improved / 88 regressed sessions,
and three gained / three lost hits. The second has 121 interventions, seven
improved / eight regressed sessions, and one gained / three lost hits: two fewer
hits overall. Preserving the per-turn candidate set does not guarantee preserving
hits across a finite conversation when ranking, questions and exposure change.

**400 separate targets with explicit fields suppressed in the new sidecar:**

| Agent | HR | MRR | Mean turns | Score |
|---|---:|---:|---:|---:|
| Current baseline | .920000 | .679366 | 2.6825 | **.830160** |
| Field-first index | .920000 | .673752 | 2.6775 | .828576 |
| Counterevidence-only index | .920000 | .679411 | 2.6825 | .830173 |

The tiny counterevidence-only gain comes from one improved session and zero
regressed sessions. Its one-sided paired bootstrap lower bound is zero; it is
not an established improvement. The suppression applies only to the new index:
shared retrieval metadata, embeddings and simulator intent cards remain original.
This tests resilience to an incomplete sidecar, not complete-agent metadata loss.

At alpha .05/8 with 20,000 bootstrap draws, language score-gain lower bounds are
-.018003 and -.009420 for the two arms. Suppression bounds are -.006769 and zero.
Both arms fail aggregate accuracy requirements; neither proceeds to timing
promotion. All runs have zero exceptions, invalid outputs and internal research
errors. Both indexes load successfully.

Public 200 responses are identical for both variants and baseline: HR 1.0,
MRR .99625, MTTC 2.35, score **.971875**. Neither variant intervenes on public
ranking. All 441 unit tests pass, including provenance, missing metadata,
negation, percentages, stale assets, current-intent overrides, candidate-set
preservation and protocol-path isolation.

## Architecture before and after

| Boundary | Architecture |
|---|---|
| Current agent before this experiment | Accepted round-six intent operations; BM25/BGE retrieval; exact evidence; protocol/Pareto planning |
| Experimental agents | Same pipeline plus a read-only attribute sidecar and an optional best-tier tie-break |
| Current agent after evaluation | Unchanged; no sidecar dependency or new ranking rule enabled |

The existing exact tier already groups products with equal exact evidence, but
their original order still carries hybrid relevance information. Replacing that
order with attribute support is an additional ranking decision, not a free
accuracy improvement. Our interpretation is that sparse metadata and redundant
keyword evidence do not supply a better tie-break here. The experiments reject
these two integrations, not structured attributes in general. Candidate-generation
rescue and richer semantic extraction were not evaluated in this round.

## Reproduce

Using a separate research output directory and the recorded source/data identities:

```
python -m scripts.build_attribute_index --output ../round7/attributes-v1.sqlite
python -m scripts.build_attribute_index --output ../round7/attributes-no-details.sqlite --omit-details
python -m unittest discover -s tests
python -m scripts.validate_attribute_experiment
```

Builders/drivers refuse to overwrite existing artifacts. Raw sessions and the
large derived indexes remain in ignored local research storage; only source,
tests and aggregate results are committed. All opened targets are consumed
evidence for future work. None is from the organizer's hidden 800, and no
competitor superiority claim follows from this experiment.

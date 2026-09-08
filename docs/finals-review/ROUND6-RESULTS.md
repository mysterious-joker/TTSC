# Round six: repair paraphrased intent changes

**Decision: adopt the bounded intent-operation repair in the personal fork.**
All four predeclared fresh accuracy gates pass. The repair resolves the audited
black-to-white correction and improves aggregate HR, MRR and turn efficiency on
three new language suites. It does not establish unrestricted language
understanding or a score on the organizer's private 800.

Baseline: `fa359373a632f07ec9caf494edfbbc4d8a2ab13f`.
Frozen runtime SHA-256:
`867c55b8e570cd399c061efd087b46889c0313b0629ec986c3968ad853e58939`.
The [plan](ROUND6-PLAN.md) records the acceptance rule and source/data boundaries;
the [aggregate bundle](round6-results-summary.json) embeds source hashes,
suite identities, comparisons and bootstrap results. No runtime source changed
after the freeze or during confirmation.

## Architecture before and after

| Layer | Before | Active repair |
|---|---|---|
| Unsupported language | Append the whole message as soft free text | Attempt bounded compositional intent operations; preserve the fallback when interpretation is uncertain or incomplete |
| Corrections | A new sentence could coexist with an obsolete hard preference | Resolve an existing value or slot, remove that requirement and retain unrelated confirmations |
| Preference removal | Dependent on a small set of whole-sentence forms | Separate withdrawal, exclusion and no-preference operations; withdrawal does not automatically ban the old value |
| Provenance | Unsupported replacement could lose its relationship to the earlier preference | Retain source/turn information, including soft replacement evidence, so another correction can withdraw it again |
| Polite answers | Some replacement sentences were interpreted as appended answers | Check explicit replacement commands before the polite-answer grammar |
| Initial requests | Some ordinary openings left category and requirement unstructured | Parse bounded request forms and typed requirements; uncertain values remain soft |
| Protocol reasoning | Strict recognition of the original transcript | Unchanged: semantic edits do not create simulator events or authorize protocol refutation |
| Retrieval and planning | BM25/BGE hybrid, exact-evidence ranking, Pareto question/slate policy | Same policies and models |

`conversational_search/intent_operations.py` bounds message length, clause count
and state collections. Commands are interpreted atomically. Quoted, hypothetical,
conditional, ambiguous and incomplete interpretations retain the old fallback.
Destructive edits increment the intent version for dependent caches and
presentation epochs. No evaluator, target IDs, scenario labels or benchmark
fixtures enter this module.

The audited sequence now produces:

```
Before: Color: black
Message: Make that white instead; black is no longer what I want.
After:  Color: white
```

A separately confirmed material remains active. Exclusions and withdrawals have
separate effects. Untyped replacement evidence remains soft and revocable.
Ambiguous cross-slot edits and combined old requirements remain conservatively
unsupported; this implementation is not a general NLU model.

## Fresh accuracy validation

The 2,800 new targets exclude 18,600 prior/reserved targets and are mutually
disjoint. Wording transforms were authored after the runtime freeze and frozen
before their outcomes were opened. The official evaluator controls disclosure,
stopping and exact-ASIN scoring. Transforms see only the message.

| Fresh suite | HR before → after | MRR before → after | Mean turns before → after | Score before → after |
|---|---|---|---|---|
| Official wording, uniform 400 | .987500 → .987500 | .977896 → .977896 | 2.6500 → 2.6500 | **.954119 → .954119** |
| New sentence forms, weighted 800 | .823750 → .918750 | .541479 → .661620 | 3.9700 → 3.1675 | **.714919 → .814511** |
| Mixed original/new forms, weighted 800 | .907500 → .956250 | .731026 → .779168 | 3.1525 → 2.7725 | **.830008 → .876425** |
| Attribute paraphrases, category-balanced 800 | .840000 → .931250 | .576952 → .680323 | 3.4025 → 2.5975 | **.745036 → .837772** |

Every aggregate accuracy component is nondecreasing on every suite. Official
responses match byte-for-byte. Paired score-gain lower bounds, using 20,000
bootstrap draws at alpha .05/8, are **.074022, .027499 and .066511** for the three
language suites. There are zero exceptions or invalid outputs. These bounds
describe uncertainty within the tested synthetic populations, not the private
purchase-derived distribution.

Trade-offs remain under the user's aggregate rule:

| Language suite | Improved / regressed / unchanged sessions | Gained / lost hits |
|---|---|---|
| New forms | 308 / 144 / 348 | 84 / 8 |
| Mixed forms | 150 / 87 / 563 | 43 / 4 |
| Attribute language | 291 / 159 / 350 | 81 / 8 |

All four scenario mean scores improve in the new-forms suite. Mixed browsing
mean score falls .009364. Attribute-language browsing falls .002270 and boundary
falls .007813. Preference-override gains dominate the overall improvement.
This is not every-session or every-scenario dominance.

## Compatibility and coverage

- Public 200 remains HR 1.0, MRR .99625, MTTC 2.35, score **.971875**; the full
  response digest remains `617ed260db8fedc5f1add9054f515afc8cfb2aac05c742794864b66b404b6417`.
- Previous language 200 retains HR .96, MRR .820218, MTTC 2.52 and score .895665.
- Previous punctuation 800 preserves complete responses and score .885367.
- 427 unit tests passed before freezing. Another 21 post-freeze state checks,
  now retained in one regression test, passed; the final suite contains 428 tests.

The new language families are authored by the same coding agent, not an
independent human paraphrase corpus. Attribute transforms include color-label
variants, grey/gray spelling, material wording and a few reviewed care/material
equivalences. Most long feature values remain unchanged. This broadens the
earlier envelope-only tests but does not validate arbitrary synonyms, implicit
product categories, complex negation or all reference resolution. No result
establishes superiority over another team.

All exposed targets and wording families are now consumed development evidence
for future changes. None of these scores comes from the organizer's hidden 800.

## Runtime after accuracy validation

Three sequential public-suite pairs alternated baseline/candidate order after
other benchmark processes had finished. All six runs preserve complete public
responses. [Timing details](round6-runtime-summary.json):

| Median measurement | Before | After |
|---|---:|---:|
| Startup plus evaluation | 15.5111 s | 15.5014 s |
| Mean response latency | 25.2329 ms | 25.2276 ms |
| p95 response latency | 47.7860 ms | 47.8080 ms |
| Process peak RSS | 653.000 MiB | 653.078 MiB |

These are effectively similar point measurements, not a proven speedup. The
mean paired session saving is negative (-.088599 ms), its one-sided lower bound
is -.161683 ms, and p95 rises .022 ms. The earlier strict runtime non-regression
gate therefore would fail. Adoption follows the user's newer accuracy-first
priority and the explicitly declared accuracy-only gate; no guarantee of zero
latency regression is made. Language confirmation timings are diagnostic only
because an earlier compatibility job overlapped part of the study.

## Reproduction

From the personal checkout, using the frozen baseline archive and data manifests:

```
python -m unittest discover -s tests
python -m scripts.validate_paraphrase_repair
python -m scripts.measure_paraphrase_runtime
```

The drivers refuse to overwrite existing output directories. Preserve those
outputs; use a separate research checkout for a new reproduction. Raw sessions
remain in the ignored local `round6` research folder.

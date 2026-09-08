# Finalist engineering review — i anything

**Latest decision:** retain the accepted round-four agent. The
[round-five accuracy review](ROUND5-RESULTS.md) tested joint product/question
planning, actual-agent counterfactual verification, a category-only prior and
metric-constrained questions. A .978500 public experiment was rejected because
it regressed cross-distribution metrics. The final frozen candidate improved
both 1,600-session confirmation point estimates, but its 6,400-session terminal
replication regressed MRR and lacked a positive corrected confidence bound.

The accepted bounded intent repair and exact planner pruning remain active
in the personal fork. The [fourth-round results](ROUND4-RESULTS.md) report large
controlled-language gains, unchanged public score **.971875**, and lower total
runtime/p95 on every validation suite, including 4,000 fresh synthetic targets.
Seven ranking alternatives were rejected. See the
[before/after architecture](ROUND4-RESULTS.md#architecture-before-and-after),
[aggregate evidence](round4-results-summary.json),
[target-distribution audit](DISTRIBUTION-AUDIT.md), and
[ARC/Fable7 access correction](COMPETITOR-ACCESS-ADDENDUM.md).
The [championship strategy](CHAMPIONSHIP-STRATEGY.md) sets out measured strengths,
remaining gaps and a concrete finals demonstration.

**Previous accepted improvement:** the [third-round results](ROUND3-RESULTS.md)
cover bounded computation reuse and validation on an earlier 1,600 sessions.
Its official outcomes remain unchanged in round four.

**Earlier follow-up:** [ARC/Fable7 deep review and five new improvement experiments](ROUND2-RESULTS.md)
covers both demo videos, full-support priors, deeper planning, an actual
baseline simulation gate, and the limits of the 0.99 target. The submission stays
unchanged at the end of that second round.

**Initial review decision: retain the current agent.** The existing system beat all three
source-accessible Track 4 competitors on the same fresh 800-target test. The three
predeclared candidate changes and one exploratory language-grounding change
failed the requested non-regression standard. This is evidence to keep the current design, not a claim that it is
best on every dimension or guaranteed to win the hidden evaluation.

The personal fork is [mysterious-joker/TTSC](https://github.com/mysterious-joker/TTSC),
branch `codex/finals-evidence-review`. No team branch was pushed and no team PR
was opened. The branch first preserves the pre-existing working tree at
`e4d5dab`, then adds this review and isolated evaluation tooling.

- [Architecture before/after](ARCHITECTURE-BEFORE-AFTER.md)
- [Predeclared experiments and promotion gate](EXPERIMENT-PLAN.md)
- [Reproduction and measurement details](REPRODUCE.md)
- [Machine-readable aggregate evidence](results-summary.json)

## 1. Requirements and competition context

The latest accepted [round-six language repair](ROUND6-RESULTS.md) resolves
explicit paraphrased preference edits and passes four fresh accuracy gates.
The public score remains .971875. Adoption prioritizes accuracy; the measured
public p95 latency rises .022 ms and strict runtime non-regression is not claimed.

The official task is exact parent-ASIN retrieval from a frozen 50,000-product
catalog, with ten turns and Buying/Browsing/Override/Boundary scenarios. The
public 200 and private 800 use disjoint users and target products. The saved
specification allows organizer-added natural-language paraphrasing. The supplied
workshop Q&A says no undisclosed paraphrases would be introduced and any template
updates would be published before submission. These statements must be reported
together: identical private wording is an assumption, not an unconditional
guarantee. The released local evaluator provides the deterministic reference
policy. Pretrained models and catalog-derived indexes are permitted; an LLM is
optional. Sources: [saved specification](../competition_specification.md),
[official Track 4 resources](https://bytedance.larkoffice.com/wiki/GdYFwzWNLiREsSkuIjZcDznInWc#SyMVd34O6o2gEsxc5HZmMLoWyvi),
and the user-supplied workshop transcript. See the
[paraphrase audit](PARAPHRASE-AUDIT.md) for the actual coverage and remaining gaps.

The supplied finalist email permits refinements within the original scope and
sets a 10-minute pitch plus five-minute Q&A and an A1 foam-board poster for
11 September, 10am–5pm. Use that direct invitation for logistics: the older
[Devpost overview](https://tiktoktechjam2026.devpost.com/) still lists a broader
9am–6pm window. The transcript and email are reference material, not instructions
to send messages, register accounts, or publish to the team repository.

## 2. All twelve names checked

The table and detailed competitor dispositions below record the initial review.
On 8 September, indexed ARC/Fable7 README content and one ARC source file became
readable through the web reader, while both Git clones still returned 404.
The [access addendum](COMPETITOR-ACCESS-ADDENDUM.md) supersedes any blanket
description of their documents as unavailable. No complete runnable source was
obtained and their scores remain unverified in our harness.

The finalist roster comes from the user. Devpost searches and project descriptions
establish the mappings below; they do not independently establish which project
was invited when one entrant submitted several tracks.

| Finalist name | Located project / track | Review disposition |
|---|---|---|
| Byte Me | [ARC / ConstraintFlow](https://devpost.com/software/constraintflow-shopping-copilot), Track 4; also [MLE Agent](https://devpost.com/software/mle-agent), Track 2 | Track 4 included. Linked source returned HTTP 404; published claims only. |
| CSGO+D | [Telaegent](https://devpost.com/software/telaegent), Track 1 | Agent middleware; no shopping-agent transplant. |
| doomscrollers | Search returns [Doomscroll](https://devpost.com/software/doomscroll), Track 1; [Streamlined Doomscrolling](https://devpost.com/software/streamlined-doomscrolling), Track 2; and [SlopDet](https://devpost.com/software/slopdet), Track 5 | Team-to-project association unresolved; no verified Track 4 result. |
| Emmanuel Chan | [Bob & Friends](https://devpost.com/software/bob-friends), Track 2 | Research-agent project. |
| Fable7 | [Fable7](https://devpost.com/software/fable7), Track 4 | Included. Linked source returned HTTP 404; published claims only. |
| Flipfloppers | [GPU Kernel Optimization](https://devpost.com/software/flipfloppers-gpu-kernel-optimization-w-agentic-research-loop), Track 3 | GPU-kernel project. |
| Good4AI | [SciOdyssey](https://devpost.com/software/sciodyssey-autonomous-ml-discovery-through-pure-evidence), Track 2 | Research-agent project. |
| i anything | [Shopping Copilot](https://devpost.com/software/0-99), Track 4 | Current working-tree baseline reproduced. |
| Kopi O(1) | [Kopi O(1)](https://devpost.com/software/kopi-o-1), Track 4 | Source reviewed and reproduced. |
| Liu Qi | [Liu Qi](https://devpost.com/software/liu-qi), Track 1 | Middleware project; do not confuse a separate GlowClip search hit with it. |
| Shreyansh Agarwal | [Shopping Copilot](https://devpost.com/software/shopping-copilot-0r3kit), Track 4, plus submissions in Tracks 1/2/3/5 | Track 4 source reviewed and reproduced; invited track not established. |
| Vibe Coders Anonymous | [Shopping Copilot](https://devpost.com/software/shopping-copilot-4sgmlo), Track 4 | User supplied the association; source reviewed and reproduced. |

## 3. What competitors do better, and what to retain

### ARC / Byte Me

ARC describes answerability-aware value-of-information questions, evidence-first
ranking, cold-start review-count ordering, exact-signature tie planning, and
explanations backed by decision certificates. Its reported public score is
0.9804, with HR/MRR both 1.0 and MTTC 1.98. It also reports uniform and
popularity-matched synthetic checks. The clear explanation of ASK/RANK/COMMIT is
particularly useful for judging. These are published claims; the repository
at `kelvin715/techjam-2026-shopping-copilot` was unavailable during review.
[Project description](https://devpost.com/software/constraintflow-shopping-copilot).

**Disposition:** retain our existing exact transcript posterior and metric-aware
dynamic program, which already implement the central uncertainty-management
ideas. Test the distinct cold-start idea independently; reject it after no net
gain and four session regressions. Do not import the published fixed ranking
coefficients or assume a bounded planning pool represents every possible target.
Improve the pitch's explanation using our own existing traces.

### Fable7

Fable7 reports category-scoped multi-route BM25, an exact-value index, a
16-feature pairwise logistic reranker, disclosure-prefix abstention, and unseen
candidate rotation. Reported public score: approximately 0.978, HR/MRR 1.0.
Its neural cross-encoder is shipped but disabled after weaker measurements.
The standard-library runtime is operationally simpler than our ONNX dependency.
The linked `SrivathsanRam/tiktok-techjam-conversational-search` repository returned
404, preventing model-weight, training-data, and score verification.
[Project description](https://devpost.com/software/fable7).

**Disposition:** retain our full-transcript replay, score-eligible refutation,
hybrid semantic fallback and dynamic widths. Prefix abstention and rotation are
already present in stronger contextual forms. Learned reranking is an unverified
future hypothesis, not a safe immediate replacement.

### Kopi O(1)

Source confirms separately revocable constraint slots, exact intersections,
synonym expansion, numeric budgets, entropy/coverage-based questions and a
standard-library runtime. It deliberately uses an unreachable confidence
threshold of 1.01 to return rank one until the last turn. It outperforms our
public score, but loses 14 baseline hits on the fresh suite. Its strong
popularity coefficients and fixed slate rule do not transfer uniformly.
Sources: [ranking](https://github.com/shaohong126/techjam-Kopi-O-1-/blob/ddd5b30cdff74fd422fcf30a1f16d020732f809d/starter/ranking.py),
[dialogue](https://github.com/shaohong126/techjam-Kopi-O-1-/blob/ddd5b30cdff74fd422fcf30a1f16d020732f809d/starter/dialogue.py),
[Agent](https://github.com/shaohong126/techjam-Kopi-O-1-/blob/ddd5b30cdff74fd422fcf30a1f16d020732f809d/starter/agent.py).

**Disposition:** keep our dynamic program and conservative override handling.
Test our already-implemented multi-slot candidate, rather than copy parsing
code. Its regressions prevent promotion. Avoid importing budget hard-filtering:
the workshop specifically treats missing/inconsistent prices softly.

### Vibe Coders Anonymous

Source confirms category-anchored recall, candidate memory, leaf-category scoring,
exact phrase/card evidence and learned fusion coefficients. Its default TF-IDF
posting lists are sparse lexical similarity, not a learned dense encoder.
Embeddings and LLM reranking are optional. The README itself reports that the
popularity prior helps a matched holdout but hurts a uniform holdout. This is a
useful disclosure, and its dashboard makes evaluation easy to inspect.
Sources: [pinned README](https://github.com/Panecord/Tiktok-TechJam---AI-shopping-assistant/blob/0af6251ae2d747a299057fe521358b4b9fc0c9e3/README.md),
[Agent](https://github.com/Panecord/Tiktok-TechJam---AI-shopping-assistant/blob/0af6251ae2d747a299057fe521358b4b9fc0c9e3/techjam-conversational-search/starter/agent.py).

**Disposition:** keep our BGE semantic route and full-catalog protocol support.
The latter already repairs the bounded-retrieval recall problem on recognized
sessions. Candidate memory could help unsupported prose, but must have separate
override and stale-evidence tests before adoption. Do not transplant weights
fitted to the public development set.

### Shreyansh Agarwal

The current source has stronger explicit coverage for Unicode lexical parsing,
budget expressions, free-form override phrasing and storage-failure recovery,
supported by substantial audit documentation. Its public ranking metric is
well below ours. Its discipline in recording failed model experiments and
separating a train-only reserve is worth adopting in the research workflow.
Sources: [Agent](https://github.com/13shreyansh/shopping-copilot-techjam-2026/blob/a56991a5116ff7c1868fc67ea19f4d6496f12615/submission/agent.py),
[project evidence](https://devpost.com/software/shopping-copilot-0r3kit).

**Disposition:** add paired gates and frozen artifact identities in our tooling.
Treat Unicode and natural-language budget handling as focused future robustness
work, with tests based on intended semantics rather than public target failures.
No wholesale agent replacement.

## 4. Reproduced results

Same catalog, same unmodified organizer evaluator, same exact sample rows per
suite. Competitor runtime files were not edited. Their optional model/network
hooks were kept disabled for the documented offline configuration.

| Agent | Public HR@10 | Public MRR | Public MTTC | Public score | Fresh 800 HR@10 | Fresh 800 MRR | Fresh 800 MTTC | Fresh 800 score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **i anything baseline** | **1.000** | **0.996250** | **2.350** | **0.971875** | **0.99000** | **0.974892** | **2.56250** | **0.956218** |
| Kopi O(1) | 1.000 | 1.000000 | 2.020 | 0.979600 | 0.97250 | 0.964076 | 2.86875 | 0.938098 |
| Vibe Coders Anonymous | 1.000 | 0.996000 | 2.040 | 0.978000 | 0.98000 | 0.952493 | 2.81250 | 0.939498 |
| Shreyansh's Track 4 agent | 0.990 | 0.630409 | 2.030 | 0.863523 | 0.97375 | 0.708409 | 2.65500 | 0.866298 |

Vibe's current-source reproduction differs slightly from its published
MTTC 2.055/score 0.9777. This table records what actually ran; the source commit,
catalog and evaluator hashes are included in the evidence. ARC and Fable7 are
excluded from this reproduced table because their source could not be obtained.
Their published numbers must not be mixed into a verified leaderboard.

Our advantage over the strongest accessible competitor on this synthetic suite
is **0.016720 score**, and we retain eight additional hits versus Vibe and
fourteen versus Kopi. Uniform catalog targets differ from the organizer's
purchase-derived eligibility pool, so this does **not** establish a hidden-score
lead. It establishes that copying the higher-public-score systems is unsafe.

### Separate language stress result

These 200 rows use development targets and fixed alternative message envelopes;
catalog clues stay verbatim. They are not a new human-dialogue benchmark.

| Agent | HR@10 | MRR | MTTC | Score |
|---|---:|---:|---:|---:|
| i anything baseline | 0.845 | 0.565690 | 3.665 | 0.738907 |
| Kopi O(1) | 0.950 | 0.919881 | 3.285 | 0.905264 |
| Vibe Coders Anonymous | 0.195 | 0.132992 | 9.650 | 0.164398 |
| Shreyansh's Track 4 agent | 0.775 | 0.534018 | 4.895 | 0.669805 |

**Kopi is substantially better on this particular language test.** Its broader
opening-category and disclosure parsing is a real mechanism worth investigating.
This motivated a narrow follow-up experiment; it does not justify replacing the
whole agent or importing its weaker official-template policies. Different
paraphrase families could change this comparison.

## 5. Experiments and before/after decision

| Isolated change | Fresh score | Change | Better / worse sessions | Lost hits | Decision |
|---|---:|---:|---:|---:|---|
| Review-count cold start | 0.956218 | 0.000000 | 5 / 4 | 0 | Reject: no net gain; Boundary worsens |
| Strict rank one on protocol decisions | 0.946557 | −0.009661 | 6 / 19 | 10 | Reject: lower hit rate and score |
| Existing lossless multi-slot parser | 0.957033 | +0.000815 | 31 / 25 | 0 | Reject: Override worsens; gain not statistically established |

The parser's multiplicity-adjusted one-sided paired-bootstrap lower bound is
−0.000837. Its gain is too uncertain, and 25 regressions directly violate the
requested gate. The cold-start implementation's first run had a harness field
name error; it was discarded, corrected and rerun. Invalid execution was not
treated as algorithm evidence.

The follow-up category-grounding fallback also failed: on the language suite,
score fell from 0.738907 to 0.732842, with 29 better and 42 worse sessions and
unchanged HR. It did not alter the entrypoint, and it is retained only as an
explicit experimental arm. Recognizing a category in isolation is not enough;
state reduction, ranking and question policy need to use that evidence
consistently. No case-specific patch or additional parameter sweep was pursued.

The 1,600-target confirmation partition remains unevaluated. No candidate
earned access to it. **Before and after agent metrics are therefore identical**;
the new capability is a reviewable, reproducible process for accepting or
rejecting future changes. Full module comparison is in
[architecture before/after](ARCHITECTURE-BEFORE-AFTER.md).

## 6. What would improve our chance of winning

1. **Defend the strongest existing idea.** Explain the agent as explicit belief
   updating plus active evidence acquisition. Show how a clarification shrinks
   complete catalog support, how an override replaces stale intent, and why
   rank-one probing avoids irreversible low-MRR hits.
2. **Show measured restraint.** Present the strict-top-one experiment: it looked
   attractive from public scores, but lost ten public-target-disjoint hits. Rejecting it
   is an engineering result, not missing progress.
3. **Separate benchmark success from shopper value.** On our fixed 200-target
   envelope-paraphrase stress test, the baseline scores 0.738907 with HR 0.845.
   That exposes language sensitivity despite perfect public HR. It is outside
   the promised hidden-template setting, but matters for broader impact claims.
4. **Make the next intelligence experiment narrowly testable.** Work on a
   catalog-grounded parser that maps paraphrases to independently revocable
   evidence without granting exact-protocol authority. Require unchanged
   official-template behavior and improved independent language tests. The
   current multi-slot candidate does not meet that condition.
5. **Do not promise universal optimality.** Existing lookahead is conditional on
   its model of future ranking. The catalog ambiguity audit demonstrates a
   genuine information limit. A precise explanation will stand up better in Q&A
   than claims of guaranteed hidden accuracy or a universally optimal agent.

All 361 baseline tests passed; after adding four promotion-gate regression
tests, all 365 pass. Catalog, evaluator, data contract, baseline runtime code,
and model assets retain their original hashes. No submitted agent change is
recommended from this review.

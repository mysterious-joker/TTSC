# What can materially strengthen i anything's finalist submission

The defensible strategy is to preserve our measured retrieval strength, make
its decisions inspectable, and reduce the cost of delivering them. We have not
established that we beat ARC or Fable7 on hidden targets. Their public source is
unavailable, and our latest accuracy experiments do not justify replacing the
current decision policies. The accepted round-three runtime optimization
preserves accuracy; its disposition and measurements are in
[ROUND3-RESULTS.md](ROUND3-RESULTS.md).

## The opportunities, in order

| Priority | Concrete change or deliverable | Why it matters | Evidence / disposition |
|---|---|---|---|
| 1 | Cache repeated clue classification, document tokens, exact category cards and count-only enumeration plans; use the existing category index | Preserve every ranking and question while reducing repeated work. This improves compute efficiency without relying on target distribution. | Accepted after identical-response checks and three sequential paired runs on every frozen suite, including the fresh 1,600. |
| 2 | Show the full evidence-to-action chain in the finals demo | Judges can distinguish engineering depth from a favorable score screenshot: complete support, eligible misses, useful questions, ambiguity and fallback. | The underlying mechanisms and action traces already exist. A focused presentation/replay is the remaining deliverable; it is not a new learned model. |
| 3 | Make the validation argument reproducible | Public-only popularity gains can hurt target-disjoint performance. Show paired outcomes, confidence bounds, frozen code/data identities and an untouched confirmation test. | Implemented in the personal research branch. Competitor comparisons are controlled only where source is accessible. |
| 4 | Isolate better natural-language revision handling as a future experiment | On our fixed paraphrase stress test, override HR is only .08; Kopi performs substantially better on the complete language suite. This is the largest measured real-user gap. | Not solved. Broadly enabling our lossless parser previously caused regressions. A future intervention should be scoped to unsupported dialogue and tested on newly authored, diverse revisions, not the existing paraphrase strings. |
| 5 | Improve question selection using actual continuation value | Some questions skip generic clues and expose a discriminating attribute sooner. The benefit depends on future ranking and what the user can answer. | Four new round-three alternatives were tested. Direct priors lose an aggregate metric; retaining baseline rank and using longer continuation has only a tiny, statistically unsupported gain. Keep experimental. |

This is an engineering priority order, not a prediction of prize placement.

## Where we can distinguish ourselves

**A recommendation should carry an explanation of what is known and what is
still ambiguous.** Demonstrate four concrete properties together:

1. **Complete coverage when the contract permits it.** Exact replay searches
   the full coarse category, including products absent from the bounded lexical
   and dense retrieval pools. An exact survivor is possible given the observed
   transcript; that does not mean it is certainly the target.
2. **Correct treatment of feedback.** A continued eligible session can disprove
   the previous displayed IDs. A pending preference override cannot. Show why
   this distinction prevents premature exclusions.
3. **Deliberate questions and output widths.** Show the predicted reply split,
   the remaining ambiguity and why rank one or a wider slate is appropriate.
   The current planner's dominance guarantee is conditional on its continuation
   model, not a universal end-to-end guarantee.
4. **Measured computation.** Tie the same visible decisions to reproducible
   CPU time, tail latency, zero model-token use and bounded cache sizes. Keep
   the hybrid fallback for inputs outside the exact dialogue contract.

ARC also presents decision certificates, and Fable7 also uses prefix matching.
Claiming that either mechanism alone is unique would be inaccurate. Our pitch
should demonstrate the complete combination and the evidence behind it. The
strength is how the system handles difficult cases, not a list of algorithms.

## A concrete demonstration sequence

Use catalog-derived examples or declared demo fixtures. Keep target truth in
the demonstrator/evaluator; the agent receives only its ordinary API inputs.
Do not imply that hand-selected demos are an independent benchmark.

| Scene | What the judge sees | What it establishes |
|---|---|---|
| Shared feature, discriminating later clue | Several possible products become one after a useful reply; show support size before and after. | Evidence accumulation and a purposeful question. |
| Preference correction | A product displayed before the correction remains eligible when appropriate; show when negative feedback is valid. | Stateful reasoning and robustness to changing intent. |
| Indistinguishable variants | The system exposes a measured slate rather than inventing a distinction unsupported by the catalog. | Honest uncertainty and finite-horizon planning. |
| Free-form request | The interface clearly shows that semantic/lexical retrieval is being used; do not label it an exact certificate. | Practical fallback and a credible boundary to the guarantee. |

Use existing traces to explain the action that actually ran. Do not draw an
idealized decision tree unrelated to the live output. Show benchmark replay
results alongside the live demonstration so temporary machine load is visible.

## What 0.99 means here

The public baseline already has HR 1.0 and MRR .99625; its score is .971875
because average first-hit turn is 2.35. With perfect HR/MRR, a .99 technical
score requires MTTC at most 1.5. A .99 turn-efficiency value requires MTTC at
most 1.1. These are different objectives, and faster code does not change MTTC.

There is also a distribution-independent timing limit for a suite containing
15% intent overrides: those sessions cannot score before turn three. Even an
oracle hitting every other session on turn one has MTTC at least 1.3, so its
turn efficiency is at most .97 (lower when some overrides occur on turn four).
Thus .99 **in every metric** is not feasible for that scenario mix. The score's
.99 target remains a separate question; it should not be confused with .99
turn efficiency. This follows directly from the eligibility check and scoring
in the unchanged `evaluator/local_evaluator.py`.

Our consumed target-disjoint 800 gives HR .99, MRR .974892 and MTTC 2.5625.
The catalog contains product groups that can emit exactly the same conversation.
No larger model can identify a particular member from absent information.
The [catalog-only observability audit](ROUND2-RESULTS.md) quantifies optimistic
population ceilings under uniform targets; it is **not** a bound on the actual
finite hidden sample or an estimate of its purchase distribution.

For an accuracy gain, the remaining sources of information are better use of
the observed text, better ranking priors that transfer to the unknown target
distribution, and more informative allowed replies. More inference without
additional information has already proved costly in the counterfactual shield.

## How this supports the final judging criteria

The event lists technical execution, innovation/problem insight, impact,
feasibility and presentation. It does not publish criterion percentages on the
overview. A higher Track 4 score alone does not establish the overall champion.
[Official judging criteria](https://tiktoktechjam2026.devpost.com/).

| Criterion | Evidence to present |
|---|---|
| Technical execution | Live difficult-case replay, response contracts, passing tests, measured runtime and a clear architecture. |
| Innovation and problem insight | Explain the distinction between semantic relevance, exact possibility and observational ambiguity; connect each to the chosen action. |
| Impact | Show reduced wasted recommendations and user effort in concrete shopping conversations. Avoid inventing conversion or revenue lift. |
| Feasibility | Offline operation, deterministic assets, bounded computation, fallback behavior and reproducible installation. |
| Presentation | One coherent problem → decision process → measured outcome story, with honest answers about private-data uncertainty. |

Suggested ten-minute allocation: 1 minute problem and shopping failure; 2 minutes
architecture; 3 minutes difficult-case demonstration; 2 minutes controlled
validation and improvements since preliminary submission; 1 minute feasibility
and limitations; 1 minute conclusion and transition to questions.

## Questions to rehearse

- **Why not a larger LLM?** The released replies are deterministic and catalog
  grounded. Exact computation is appropriate there; learned interpretation
  remains useful for unrestricted language, where our stress test shows work
  remains. Do not claim the fallback solves every free-form request.
- **Are you overfitting the public 200?** Show target-disjoint construction,
  frozen hypotheses, rejected public-score improvements and untouched validation.
  These reduce overfitting risk; they do not prove performance on unknown labels.
- **Do you beat ARC and Fable7?** Their reported public scores are higher. Their
  source was unavailable for controlled reproduction. State our controlled
  comparisons and our own improvements without converting claims into wins.
- **What changed since preliminary submission?** Name only the changes actually
  accepted in ROUND3-RESULTS.md and show before/after evidence. Keep experimental
  planners out of the release story.

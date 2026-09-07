# Frozen experiment plan — 7 September 2026

Baseline: preserved working tree at `e4d5dab`, based on team commit `5378908`.
The baseline includes changes already present when this review began. They are
not improvements produced by this review. The entrypoint remains unchanged.

## Hypotheses fixed before inspecting candidate results

1. **Cold-start review count.** ARC and Kopi describe a review-count prior before
   any constraint; Vibe reports a popularity/long-tail trade-off. Independently
   sort the existing candidate pool by review count only on turn one with no
   active requirements or exclusions. Preserve exact-evidence ranking and the
   complete protocol support. No learned coefficient or ASIN exception.
2. **Strict rank-one exposure.** Kopi uses rank one until turn ten. Test replacing
   only our protocol enumeration/Pareto widths with one before turn ten. Keep
   state and refutation synchronized with what is actually shown. Do not
   change unsupported-language output gates.
3. **Existing lossless multi-slot parser.** Competitors emphasize independently
   revocable slots. Our repository already has this disabled candidate; test
   it instead of importing another team's parsing code or inventing a new one.

No competitor code is copied into the agent. Downloaded source is local research
material; it is not included in the personal branch.

## Data boundaries

- Public 200: contaminated development evidence, useful only for regression and
  reproducing published claims. Never a promotion criterion by itself.
- Generate 2,400 distinct targets uniformly from catalog IDs excluding the public
  200, seed `202609071`, using the pre-existing suite generator.
- First 800: development; SHA-256
  `de848394915b253890989e487860cef98d776f339d8011cd64d571032bea2b60`.
- Remaining 1,600: reserved confirmation; SHA-256
  `1c4c233584a0599786ebf833e09c22c638742718d04bea6b004dae0cd61dc0ae`.
- The 2,400 combined suite has the official 40/40/15/5 scenario mix. Its two
  random subsets have their actual measured counts reported, not an assumed
  exact mix.
- Language stress: first 200 development rows, with fixed alternative message
  envelopes in `scripts/benchmark_finalists.py`. Catalog values remain exact;
  this tests wrapper sensitivity, not unconstrained human conversation.
- All synthetic sessions share the released simulator and catalog. They are
  not the organizer's 800 hidden sessions, are not drawn from the organizer's
  purchase-eligibility pool, and cannot estimate that private distribution.
- No target labels, sample IDs, or scenario labels enter `reset`/`respond`.
  Each runtime arm executes in a fresh process against the unchanged evaluator.

## Promotion gate

A candidate needs a strict TechnicalScore improvement, no individual-session
utility regression, no lost hit, no scenario aggregate regression, no new
exceptions or invalid outputs, and no stress-suite regression. The one-sided
paired bootstrap lower bound must exceed zero; account for the three screened
candidates with alpha = 0.05 / 3. Confirmation is run once only for a candidate
that clears development. Rerun all repository tests before promoting it.

Latency is diagnostic on concurrently executed development jobs, not a fair
hardware race. A final latency claim requires sequential measurement.

Any failed gate leaves the submission system unchanged. Even passing every gate
would establish measured evidence, not a guarantee over unseen targets or
unmodeled language. A universal guarantee would require stronger assumptions
and a proof that models the actual future reranking and interaction policy.

## Follow-up hypothesis, declared after the first three experiments

The fixed-envelope stress comparison showed Kopi substantially ahead of our
fallback. Its category parser explicitly supports more natural opening forms.
One additional exploratory arm, `catalog_category`, recognizes a unique longest
catalog category phrase in the first clause only when our parser and strict
protocol recognizer both do not already understand the opening. Negated and
ambiguous category mentions fail open. It never rewrites a message into a
protocol template or changes recognized official openings.

This hypothesis uses the now-consumed language development suite. It is not a
precommitted independent validation result. A regression on that suite rejects
it immediately. Only a clean development win would justify testing new language
forms and targets plus official-template invariance on the reserved set. No
parameter sweep or exception based on individual target failures is allowed.

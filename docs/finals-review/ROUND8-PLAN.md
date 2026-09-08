# Round eight: competition-first conversation correctness

Baseline: `749f695ac302f639147729550eab1d2576e43591`. The user selected
competition-agent improvements over a new shopping frontend. The supplied
eight-point brief is treated as priorities, not evidence that its old-source
observations still describe the current fork.

## Candidate and scope

One bounded candidate combines:

- Whole-message parsing for simple apparel openings containing independently
  stated color, material and maximum budget. Every token must be accounted for;
  unknown modifiers, brands, alternatives and negation use the existing fallback.
- Explicit edits that preserve unrelated preferences, polite exclusions, and
  rejection of ambiguous singular references to several earlier requirements.
- Preservation of explicit importance cues, with price ceilings independent of
  a preference for a particular color/material.
- Truthful response wording for empty or degraded retrieval, without changing
  recommendation IDs or question choice.

This is a finite grammar with domain vocabulary, not a model-assisted general
parser. No model, learned ranking, hard attribute filter, disclosure-card policy,
personalization weight, or human question policy is added. The rejected
round-seven attribute ranking remains disabled. The official evaluator is not
modified. No hidden data or competitor outcome is used.

## Freeze and acceptance

Archive the baseline and freeze all runtime source plus evaluation wording
before opening confirmation outcomes. There is one candidate, no threshold
sweep. The independently authored intent corpus (52 conversations) was written
by a separate agent without reading the parser/tests, and remains unopened by
implementers until the freeze. Its SHA-256 is
`20ff7ec7c00fd78d937d4fe653eaeaa12022a60e192ac52eaf7e341088d9db1c`.
It is model-authored, not a human study or random sample of real shoppers.

Acceptance requires:

1. All tests pass; no newly introduced unsafe destructive interpretation on
   independent intent checks. Compare complete expected semantics using the
   prewritten expectations, retain both outputs, and disclose unsupported cases.
2. Public 200 and 400 fresh official-wording sessions preserve complete responses
   in normal retrieval. No gain is required on an unchanged path.
3. On 800 fresh end-to-end language targets, HR, MRR and turn efficiency must
   not regress and paired score improvement must have a positive one-sided
   20,000-draw bootstrap bound at alpha .05/4. Newly sampled targets exclude all
   22,600 earlier/reserved targets. Profiles are sampled independently.
4. Check the consumed round-seven 800 language targets for compatibility,
   explicitly without presenting them as fresh confirmation evidence.

The new end-to-end wording preserves catalog clue values. Simple color/material
openings move an explicit clue before the category noun; overrides add an
explicit retain-other-preferences clause. These declared language families are
development-derived, not a claim of arbitrary paraphrase generalization.

Accuracy is first, following the user's priority. If accuracy passes, measure
sequential alternating runtime pairs without other benchmark jobs. Report
response time and memory rather than assume a speed benefit. If accuracy fails,
retain unproven behavior as disabled research and report the reason. Corrections
to misleading failure copy may ship independently of ranking promotion.

Do not tune after reading fresh outcomes. Later repairs require a new freeze and
fresh evidence; opened targets and wording become consumed development data.

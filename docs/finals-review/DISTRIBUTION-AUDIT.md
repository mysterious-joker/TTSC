# Public-score gaps are not proof of overfitting

The public targets differ substantially from uniformly sampled catalog products.
This changes how useful a popularity prior can be. All figures below use the
unchanged catalog's `rating_number` field and aggregate target features only.

| Sample | Targets | Median reviews | 25th percentile | 75th percentile |
|---|---:|---:|---:|---:|
| Organizer public set | 200 | 6,846 | 986 | 18,915 |
| Earlier uniform development | 800 | 12 | 4 | 60 |
| Round-four square-root-review-weighted development | 800 | 130.5 | 28 | 576 |
| Round-four category-balanced development | 800 | 13 | 4 | 56 |

The supplied workshop transcription describes targets selected from eligible
historical purchase/review records, using earlier history for aggregate profiles.
That is different from drawing each frozen catalog product with equal chance.
This audit does not identify or reconstruct the organizer's eligible target pool,
private target labels, or purchase histories.

## What the previous experiments actually show

Our all-turn review-count prior raised public score from .971875 to .979750,
but reduced uniform-development score from .956218 to .955741. The first-turn
variant reached .977775 publicly and .956030 on uniform development. These are
distribution-sensitive trade-offs. They do not establish that the public gains
are illegitimate, that competitors memorized labels, or that uniform validation
predicts the final standings better.

Our reproduced public result finds all 200 targets but only 33 on turn one.
Kopi finds 79 on turn one and Vibe 72. Kopi finishes 58 sessions earlier and
10 later, saving 66 turns overall; 63 of those net turns come from buying and
browsing. Our review-prior experiment finds 78 on turn one. Early ordering is
a demonstrated weakness on the public population, rather than an architectural
ceiling or evidence of an undisclosed competitor model.

## Limits of the broader validation

The new square-root-weighted sample is still much less popularity-concentrated
than the public targets. Category balancing tests smaller categories more often.
All synthetic profiles are independent of the sampled targets, so these suites
do not validate profile/purchase correlation. They are coverage and sensitivity
tests, not replicas of the hidden 800.

A fresh target split protects against direct target reuse. It does not prove
that the selected sampling distribution matches the organizer's population.
Paired confidence intervals quantify uncertainty within a tested distribution;
they cannot remove this population mismatch.

We retain the user's aggregate non-regression requirement rather than quietly
relaxing it after seeing favorable public results. All seven new/revisited
ranking hypotheses failed an aggregate development metric and remain disabled.
Their results belong in the research record, not in a claim of a guaranteed win.

## Implication for the final presentation

Present reproduced same-suite comparisons as measurements, identify reported
competitor numbers as unverified when source is unavailable, and distinguish
public, synthetic official-template, and language-robustness results. Do not say
we beat ARC/Fable7 on hidden targets or that their public scores prove overfitting.
Our independent uniform-sample advantage is real on that sample, with limited
predictive scope. The latest runtime and language changes must be described by
their own measured effects; they do not inherit an accuracy gain from a rejected
ranking experiment.

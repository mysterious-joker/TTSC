# Competition-first priorities

The immediate objective is to strengthen the competition agent. Frontend work
is deferred. Improvements must support the submission's practical value and
technical contribution under the [official judging criteria](https://tiktoktechjam2026.devpost.com/#judging-criteria),
with claims limited to observed evidence.

This is a scope map; the [round-eight report](ROUND8-RESULTS.md) records acceptance
and limitations. Its bounded correction fixes pass four end-to-end gates, while
the independent 52-case language challenge shows no improvement. The prior accepted baseline includes the
[round-six prose repair](ROUND6-RESULTS.md); the pasted assessment predates that
repair in places. The [round-seven attribute integrations](ROUND7-RESULTS.md)
were rejected and remain disabled.

## 1. Reliable conversation understanding

The [intent reducer](../../conversational_search/intent.py) already stores
independent requirements, exclusions, importance, provenance and intent epochs.
Round six added atomic add/replace/withdraw operations for bounded prose.
Round eight adds [composed apparel openings](../../conversational_search/composed_request.py):
for example, category, color, material and maximum budget in one request. It
also refines [preference edits](../../conversational_search/intent_operations.py),
preserves explicit importance cues and supports “keep everything else” beside
a valid edit. Unknown modifiers, alternatives and incomplete interpretations
retain the fallback path. Arbitrary language, ambiguous references and “the
second one” remain unresolved; no model-assisted parser is introduced.

## 2. Trustworthy product evidence

The [retriever](../../conversational_search/retrieval.py) supplies product text
and reconstructed disclosure cards; these are different evidence sources.
The [exact comparator](../../conversational_search/exact_evidence.py) treats
missing or unparseable prices as unknown, not confirmed affordability. This
does not establish complete material composition or variant availability.

The experimental [attribute index](../../conversational_search/attribute_index.py)
retains source fields and polarity, but its ranking changes failed validation.
It also needs further extraction work before supporting trustworthy claims:
“cotton-like” can produce cotton evidence, and a truncated raw excerpt can omit
the matched text. This round changes neither extraction nor evidence ranking.
A future evidence layer should preserve the actual supporting span and explicit
unknown/conflict states before being evaluated for ranking or explanations.

## 3. Requirement satisfaction and trade-offs

BM25 and BGE already contribute complementary retrieval evidence. The active
[ranking pipeline](../../conversational_search/ranking.py) preserves their
useful ordering beneath exact evidence tiers. The separate
[importance-aware comparator](../../conversational_search/requirement_satisfaction.py)
implements full/partial/unknown/violated assessments but is inactive after
unsuccessful validation. Round eight improves the intent supplied to existing
ranking; it does not activate that comparator, hard filtering or automatic
constraint relaxation. Candidate-pool recall and ranking quality should remain
separate diagnostics. A future relaxation proposal must identify a supported
conflict rather than infer one from missing metadata.

## 4. Adaptive clarification

The [adapter](../../starter/agent.py) selects repeated `other` questions, while
the [exposure planner](../../conversational_search/exposure.py) can choose
presentation width and questions under exact disclosure-card assumptions.
This is useful simulator-aware decision-making, not a demonstrated human
answerability model. Round eight leaves both policies unchanged. The next
question experiment should focus on free-form turns, unresolved preferences,
catalog coverage and likely decision benefit. It should measure unnecessary
questions and recommendation quality, with exact-protocol behavior protected.

## 5. Visible, correctable preferences

There is no frontend in this repository. Immutable session state and the
[service's diagnostic hooks](../../conversational_search/service.py) provide a
starting point for a future preference editor and comparison view. Round eight
improves supported conversational edits; it does not ship editable chips,
product comparisons or source-backed recommendation explanations. Those product
features remain deferred while competition-agent work takes priority.

## 6. Dimension-specific personalization

The [profile residual](../../conversational_search/service.py) is bounded and
uses a global gate: any active requirement disables it. Explicitly choosing a
color therefore also disables residual preferences on other dimensions.
Round eight retains this behavior. Dimension-specific precedence requires its
own evaluation, especially around feedback and overrides; continued conversation
must not become assumed human rejection merely because simulator refutation
uses eligible continuations.

## 7. Generalization and user-value evidence

Public sessions alone cannot establish robustness to organizer paraphrasing.
Validation should distinguish fresh target products from genuinely independent
language, and include negation, unknown modifiers, conflicting edits and
missing metadata. Round eight improves declared correction forms on fresh targets,
but both versions fail all 52 independent complete-intent checks. That evidence
does not establish broad language understanding. Human shopping tasks and keyword-search
comparisons are subsequent evidence work. Successful task completion,
requirement violations and time to an acceptable product complement target-ID
metrics; conversion benefits remain unmeasured.

## 8. Engineering and truthful behavior

Round eight changes [response wording](../../conversational_search/service.py)
so empty searches do not claim to show matches and catalog fallbacks are
identified as options to review. Product IDs, questions and state remain under
the existing policies. Session cleanup is still absent. Sequential interleaving
has tests, but the shared SQLite connection and mutable service stores do not
justify a concurrent-instance claim. Cleanup, deployment serialization and
fresh resource measurements remain distinct engineering work; none is claimed
as completed by this candidate.

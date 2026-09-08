# Independent intent corpus: frozen-state adjudication

**Neither implementation completely satisfies any of the 52 prewritten semantic cases.** Baseline and candidate have identical final states in all 52 cases and identical states after all 85 messages. Both runs completed without errors. There is **no observed language-generalization improvement on this corpus** and no newly introduced state differences or errors. These are 52 unchanged pre-existing failures, zero observed improvements, zero observed regressions, and zero candidate-introduced destructive edits on the supplied traces.

| Runtime | Pass | Fail | Error | Unscorable |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0 | 52 | 0 | 0 |
| Candidate | 0 | 52 | 0 | 0 |

Each case started with a fresh `IntentState`. Each successive user message was passed to `apply_user_message(state, message, turn)` using its default parsing policy. The requested Python interpreter ran baseline and candidate in separate processes. No question context, product list, or photo context was injected.

The same model authored the expectations before implementation freeze and adjudicated them afterward. The corpus was authored without reading runtime/parser code or existing tests. This is independence from implementation during authorship, **not human validation** or an independent-human judge.

## What the states show

Both runs end with 33 null categories. Their final requirements contain 66 untyped entries and one entry typed as color; no final material or budget requirement is typed. Only one case has a nonempty exclusion list. Initial extraction failures dominate the results and mask many edit-specific scenarios.

- Case 008 asks for a white ceramic table lamp, then raises the ceiling from US$120 to US$160. Both states keep the initial description, including US$120, in `category`; the new ceiling is an untyped entry.
- Case 022 initially excludes white and cream, then permits white while still excluding cream. Both states retain `excluded = ['white and cream']`.
- Case 029 explicitly identifies Orange as a brand and requires black headphones. Both states assign the clarification 'Orange is the brand name, not the color' to `attribute=color` as a preference; black and the budget are not resolved.
- Case 034 clearly raises the ceiling to US$220 while referring to an unavailable second item's color. Both clauses remain one untyped entry, so the independent budget edit is not represented. There is no candidate-only deletion.
- Case 048 changes the maximum from US$150 to US$120 to US$140. Both states retain all three messages as untyped entries, with no resolved final budget.

## Scoring and limitations

The full prewritten expectation, notes, and semantic extension were used. Equivalent phrasing is accepted; exact spelling and JSON representation are not required. A complete pass does require active category, attribute, preference, exclusion, and edit meaning to be resolved in the intent state. Keeping an entire command or conversation as untyped free text does not meet that requirement. No failure relies solely on the literal `strength='soft'` field. Individual required-versus-preferred clauses must have the correct meaning and scope.

No case was unscorable after reading its notes and semantic extension. Those additions explicitly disambiguate blue OR white versus black AND white, mesh-back scope, the combined price for two cushions, soft preferences, and unsupported references. The attribute arrays alone would be an insufficient automatic oracle; the expectations were not changed to fit the runtime.

- All 52 conversations are model-authored English examples, mostly furniture/home goods, apparel, and accessories. This is not a representative random sample or a multilingual evaluation.
- The parent identified the task's frozen catalog as apparel after this corpus was authored. Many cases request products beyond that catalog. This is a scope limitation, not a reason to exclude cases or change expectations after observing results; all 52 remain in the reported denominator.
- The author also adjudicated the cases; independence concerns implementation exposure during authorship, not independence of judges. No human reviewed these labels.
- The evaluation calls only apply_user_message on IntentState. It does not evaluate downstream retrieval, product ranking, LLM interpretation of free text, or end-to-end user success.
- No synthetic last_asked_attribute or product/photo context was added. The corpus consequently exposes weak initial natural-language extraction, which masks many intended edit-specific checks.
- Every case fails complete semantic correctness, so this set has a floor effect and cannot establish which implementation handles typed edit scenarios better. Exact trace equality supplies only a bounded no-change observation.
- Expectation arrays need their notes and semantic extensions for preferences, OR/AND, material scope, total budgets, appearance, brand, scent, and unresolved references. No expectations were revised after observing outputs.
- Counts are descriptive for these 52 cases. There is no statistical significance, hidden-benchmark, hidden800, or population-performance claim.

## All-case disposition

Every row is an unchanged pre-existing failure. There are no runtime errors or candidate-only state changes. Preservation-sensitive cases are not counted as successful merely because both runtimes fail identically.

| Case | Baseline | Candidate | Evidence and semantic mismatch |
| --- | --- | --- | --- |
| independent-001 | Fail | Fail | Category is null; dark blue, cotton, and the US$35 ceiling remain inside one untyped request rather than active attribute constraints. |
| independent-002 | Fail | Fail | Category is null; the mesh-back scope, navy blue, and US$250 ceiling are not represented as resolved constraints. |
| independent-003 | Fail | Fail | The only positive requirement is the coffee-table category, but category remains null. Preserving the request as untyped text does not resolve that category. |
| independent-004 | Fail | Fail | Category is null; required oak and the US$900 ceiling are not separated from the expressly optional white preference. |
| independent-005 | Fail | Fail | Category is null; required black and the US$80 ceiling are not separated from the canvas preference and permission to use nylon. |
| independent-006 | Fail | Fail | Both original request and correction remain untyped. The state does not resolve linen's downgrade to preference while retaining required green and US$45. |
| independent-007 | Fail | Fail | Category is null and blue/cotton/US$100 are untyped. No hard navy exclusion is added, but the required constraints and soft navy aversion are not resolved separately. |
| independent-008 | Fail | Fail | Category contains the whole initial description, including the old US$120 ceiling. The US$160 replacement is untyped; white, ceramic, and the active new budget have no typed constraints. |
| independent-009 | Fail | Fail | Category is null; brown leather and both inclusive price bounds remain untyped. Neither the US$40 floor nor US$70 ceiling is represented as a budget constraint. |
| independent-010 | Fail | Fail | Category is null; both the friend's US$300 and user's US$180 occur in one untyped request. The user's active ceiling and grey wool requirements are not resolved. |
| independent-011 | Fail | Fail | Category still contains the initial US$400 description. The SGD correction is untyped; no budget constraint represents the final S$400 ceiling, and black/steel are also untyped. |
| independent-012 | Fail | Fail | Category is null. The old US$60 request and price-cap withdrawal coexist as untyped entries; red and silk are not represented as the remaining required attributes. |
| independent-013 | Fail | Fail | Category is null; white, solid oak, and US$150 remain untyped. The solid-oak requirement is not available as a resolved material constraint. |
| independent-014 | Fail | Fail | The category remains the initial blue-cotton-rug description instead of curtains. The category replacement and preserved attributes exist only in untyped update text. |
| independent-015 | Fail | Fail | Category is null; yellow linen, quantity two, and the US$60 combined ceiling remain untyped. The state does not represent a total budget for the pair. |
| independent-016 | Fail | Fail | Category retains the initial cotton-tote description. The canvas replacement is untyped, with no material constraint resolving canvas or typed black/US$30 constraints. |
| independent-017 | Fail | Fail | Category is null. Both the old white description and black replacement remain untyped; the final required black/metal/US$110 state is not resolved. |
| independent-018 | Fail | Fail | Category is null. The original green request and subsequent any-color permission remain untyped; retained glass and US$50 are not represented as attribute constraints. |
| independent-019 | Fail | Fail | Category retains the wool-coat description while the wool withdrawal is untyped. The state does not resolve the remaining navy and US$220 requirements without requiring wool. |
| independent-020 | Fail | Fail | Category retains pink and linen in the initial description. Color/fabric withdrawals and the retained US$140 ceiling are untyped, with no resolved active budget. |
| independent-021 | Fail | Fail | The no-black/no-leather turn is stored as an untyped preference and excluded is empty. Required wood and US$130 also lack typed constraints. |
| independent-022 | Fail | Fail | Excluded remains the single string 'white and cream' after white is permitted. The white exclusion is not withdrawn; cotton and US$75 also lack typed constraints. |
| independent-023 | Fail | Fail | Category is null and excluded is empty. The state does not separate the hard black exclusion and ceramic/US$25 requirements from the soft blue preference. |
| independent-024 | Fail | Fail | Category is null and excluded is empty. Cotton-free is not represented as a cotton exclusion; black and US$20 are also untyped. |
| independent-025 | Fail | Fail | Category is null and excluded is empty. Required linen and white, the US$85 ceiling, and the cotton-free exclusion are not represented separately. |
| independent-026 | Fail | Fail | Category is null and required beige/US$100 are untyped. No spurious typed linen requirement appears, but the correct appearance-versus-fiber semantics and active constraints are not resolved. |
| independent-027 | Fail | Fail | Category is null and required white/US$40 are untyped. No spurious typed wood requirement appears, but material freedom and the separate wood-like appearance request are not resolved. |
| independent-028 | Fail | Fail | Category is null and no budget constraint represents US$25. No spurious typed blue requirement appears, but blueberry scent and unrestricted color remain opaque request text. |
| independent-029 | Fail | Fail | The category absorbs the brand/color/budget description, while 'Orange is the brand name, not the color' is incorrectly assigned attribute=color as a preference. Required black and US$100 are not resolved. |
| independent-030 | Fail | Fail | Category is null; the explicitly disambiguated orange color, ceramic material, and US$30 ceiling remain one untyped request. |
| independent-031 | Fail | Fail | Initial green/velvet/US$900 are embedded in the category description rather than typed requirements, and the unsupported color reference is appended untyped. The promised required-attribute state is absent; no new destructive edit is observed. |
| independent-032 | Fail | Fail | Initial brown/leather/US$500 remain in a category description, and the unsupported photo-material reference is untyped. The required-attribute state is absent; no new destructive edit is observed. |
| independent-033 | Fail | Fail | Initial white/cotton/US$95 remain in a category description; 'second one' is appended as untyped text. The complete expected state is absent, although the candidate does not alter the baseline trace. |
| independent-034 | Fail | Fail | Category is null. The clear US$220 budget change and unresolved color-reference clause remain in one untyped entry, so the independent budget edit is not represented. |
| independent-035 | Fail | Fail | Category retains black and US$70 from the initial request. The clear white edit and price withdrawal are untyped together with the unresolved material reference; the expected white/metal/no-budget state is not resolved. |
| independent-036 | Fail | Fail | Category retains blue and US$40. The explicit cream/US$30 replacements and linen preservation are untyped, leaving no resolved final color/material/budget constraints. |
| independent-037 | Fail | Fail | Category is null and excluded is empty. The cotton withdrawal, continuing linen exclusion, and silk preference are untyped rather than independently resolved; required white/US$65 are also absent as typed constraints. |
| independent-038 | Fail | Fail | Category retains leather from the initial description. The leather prohibition and canvas replacement are untyped, excluded is empty, and black/US$50 lack typed constraints. |
| independent-039 | Fail | Fail | The initial category description is preserved, but white/wood/US$200 lack typed constraints. The alternative-price question is additionally stored as an untyped preference despite the explicit instruction to keep the request unchanged. |
| independent-040 | Fail | Fail | Category is null and green/cotton/US$35 lack typed constraints. The hypothetical future-blue statement is appended as an untyped preference rather than being kept outside active shopping preferences. |
| independent-041 | Fail | Fail | Category is null. Old red/plastic and new white/wicker attributes occur together in an untyped entry, with no resolved new-item category, material, color, or US$55 ceiling. |
| independent-042 | Fail | Fail | Category is null. Room-context attributes and the desired white/metal filing-cabinet requirements remain in one untyped entry, with no resolved US$180 budget. |
| independent-043 | Fail | Fail | Category retains the initial black description. The explicit white replacement and black prohibition are untyped, excluded is empty, and steel/US$85 lack typed constraints. |
| independent-044 | Fail | Fail | Category is null; ceramic and US$45 are untyped. No resolved color condition expresses the explicitly allowed blue OR white alternatives. |
| independent-045 | Fail | Fail | Category is null; cotton and US$30 are untyped. No resolved condition requires black AND white together in stripes on the same scarf. |
| independent-046 | Fail | Fail | Category retains blue from the original description. The any-color relaxation and continued blue preference are untyped, and required cotton/US$80 lack typed constraints. |
| independent-047 | Fail | Fail | Category is null. Mesh's promotion from preference to must is untyped, with no resolved material requirement; the remaining soft grey preference and US$190 ceiling are not separated. |
| independent-048 | Fail | Fail | Category is null. US$150, US$120, and US$140 remain in successive untyped entries; no budget constraint identifies only the final US$140 ceiling, and brown/leather lack typed constraints. |
| independent-049 | Fail | Fail | Category retains the initial black description; white and then green edits are untyped. The final green color and preserved metal/US$70 are not represented as resolved attribute constraints. |
| independent-050 | Fail | Fail | Category is null and white/ceramic/US$35 remain untyped. The acknowledgment is appended as another untyped preference rather than leaving a resolved request unchanged. |
| independent-051 | Fail | Fail | Category is null and excluded is empty. The remaining wool exclusion is not represented, nor are grey and US$160 resolved; permission to use leather is untyped. |
| independent-052 | Fail | Fail | Category is null. Required blue/cotton, the hard US$50 ceiling, and the soft US$35 price target remain untyped instead of separate requirements and preference. |

## Artifacts and provenance

- Frozen expectations: [independent-intent-cases.json](independent-intent-cases.json)
- Baseline per-turn states: [intent-baseline.json](intent-baseline.json)
- Candidate per-turn states: [intent-candidate.json](intent-candidate.json)
- Machine-readable adjudication: [intent-adjudication.json](intent-adjudication.json)
- Collection procedure: [run_intent_corpus.py](run_intent_corpus.py)
- Report generation and model findings: [build_intent_adjudication.py](build_intent_adjudication.py)

Corpus SHA-256: `20ff7ec7c00fd78d937d4fe653eaeaa12022a60e192ac52eaf7e341088d9db1c`.

Imported baseline `intent.py` SHA-256: `9d5ebcb923e2b2029e0de54f062df3ea1c0b82c09007cd1457305793ec6ceba0`.

Imported candidate `intent.py` SHA-256: `8b3054981d9c1b608e03b8c4566a9832d14f4a6b093652f9a19f9bc2825dc5b7`.

Root-reported implementation-freeze hash: `e2ad2c8a126270cdd916151703e1456847d2319523cb5910c0de88c0a587f4b7`. This is recorded as supplied; its scope need not equal the imported-module file hashes.

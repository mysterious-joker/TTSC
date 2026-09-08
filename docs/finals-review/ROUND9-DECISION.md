# Round nine: generative experiment removed

The user requested complete removal of the generative intent approach. The
experiment has been stopped and removed. The competition entry point retains
the accepted round-eight deterministic intent, BM25/BGE retrieval, evidence
ranking and question/planning architecture.

Removed locally:

- Experimental model, interpreter, transaction validator, worker, adapter,
  benchmark drivers, reporting helper and their dedicated tests.
- The service hook introduced solely for that adapter; `service.py` is restored
  exactly to the accepted `aecc8f3` version.
- The experiment dependency manifest and installed `llama-cpp-python` package.
- Both generative model assets, totaling 3,779,720,384 bytes of model weights.
- The experiment's research copies, prompts, logs, outputs and provisioning docs.
- Stale bytecode for the removed modules. Both inference processes and their
  workers have exited.

These experimental source files were never committed or pushed. No generative
provider is enabled, and `llama_cpp` is no longer importable in the project environment. BGE's local
embedding encoder and its ONNX runtime remain; they are part of the established
retrieval pipeline. Separate third-party competitor research and historical
competition documentation are reference material, not our runtime integration.

## Verification after removal

All 457 existing tests pass. The complete 200-session public benchmark also
passes with zero exceptions, invalid outputs or generative token usage.

| Metric | Accepted agent | After removal |
|---|---:|---:|
| Hit rate | 1.000000 | 1.000000 |
| MRR | .996250 | .996250 |
| Mean turns | 2.350000 | 2.350000 |
| Technical score | .971875 | .971875 |

All 470 responses match the accepted agent's response SHA-256 exactly:
`617ed260db8fedc5f1add9054f515afc8cfb2aac05c742794864b66b404b6417`.
See [the complete verification record](round9-public-verification.json).

The static [independent intent cases](intent-language-cases/README.md) contain
inputs and expected meanings only. They require no model dependency and are
retained for future deterministic parser diagnostics. Treat them as consumed
data. The stopped model trial supplies no accepted fresh accuracy estimate.

This cleanup preserves the accepted architecture and benchmark behavior. It does
not itself establish improved natural-language understanding or hidden-session
performance. Further improvements will work within the non-generative agent.

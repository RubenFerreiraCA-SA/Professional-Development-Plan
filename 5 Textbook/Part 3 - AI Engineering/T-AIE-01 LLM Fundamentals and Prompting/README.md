# T-AIE-01 — LLM Fundamentals and Prompting

*Part 3 — AI Engineering*

A large language model is a component that produces fluent, plausible text from the text it is given: useful, mutable and unreliable in ways that are statistical rather than reproducible. Treating it as an interface with a contract, a distribution of behaviour and a bounded authority explains most of what follows in this chapter.

## Levels


- [Beginner Foundations](T-AIE-01-B%20Beginner.md#t-aie-01-b) — next-token prediction, tokens, the context window, training versus inference, temperature, hallucination, roles, a first scoped prompt and a first honest prompt experiment.
- [Intermediate Practice](T-AIE-01-I%20Intermediate.md#t-aie-01-i) — prompt structure, delimiting inputs, output schemas and validation, bounded repair, pre-checks, offline fake models, prompt versioning, latency and cost estimation, a troubleshooting routine.
- [Professional Engineering](T-AIE-01-P%20Professional.md#t-aie-01-p) — bounded AI features, release bundles, prompt-injection boundaries, defensive handling of outputs, model selection, privacy, acceptance standards, budgets, kill switches and operations.
- [Expert Depth](T-AIE-01-E%20Expert.md#t-aie-01-e) — failure across models, evaluation validity and statistics, the security model, token economics, lifecycle and drift, uncertainty, calibration and abstention, model-limits assessments.

All examples use a neutral read-only `ops-assistant` over runbooks for an `orders` service; the chapter has no dependency on any other course material. Numbers, prices and thresholds marked *illustrative* or shown as placeholders demonstrate calculations and shapes, not measured results of any model or provider.

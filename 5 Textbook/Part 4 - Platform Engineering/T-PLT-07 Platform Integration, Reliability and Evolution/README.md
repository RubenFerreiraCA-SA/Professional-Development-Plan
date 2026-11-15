# T-PLT-07 — Platform Integration, Reliability and Evolution

*Part 4 — Platform Engineering*

A platform is not its components; it is the contracts at the seams between them. Most platform defects are integration defects, found where one component hands an artefact to the next, and most platform outages are control-plane failures that stay silent until someone needs to change something. This chapter teaches you to follow one change across the whole path, to design recovery for the delivery system itself, and to evolve the platform without breaking the people who depend on it.

## Levels


- [Beginner Foundations](T-PLT-07-B%20Beginner.md#t-plt-07-b) — how repository, build, registry, infrastructure, delivery, identity and monitoring connect; a plain architecture walkthrough; artefacts that cross each boundary; tags versus digests; evidence over claims; the integration checklist; a first planted failure.
- [Intermediate Practice](T-PLT-07-I%20Intermediate.md#t-plt-07-i) — the lifecycle from onboarding to deploy, monitor, rollback and feedback; verify-then-trust checks; the three-way digest match; failure signals per stage; responsibility matrix; walking a symptom backwards; stateful drills and runbooks.
- [Professional Engineering](T-PLT-07-P%20Professional.md#t-plt-07-p) — end-to-end architecture with control and data planes; dependency and recovery tables; bootstrapping; platform SLOs; scoped identity and secrets; negative testing; ownership; tested runbooks; claims ledger; seam checklist; trade-offs.
- [Expert Depth](T-PLT-07-E%20Expert.md#t-plt-07-e) — whole-platform failure propagation and shared fate; cross-domain policy layers and exceptions; versioning, deprecation and bulk migration; core-component migration and cells at organisational scale; independent-user validation; hard design cases.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.

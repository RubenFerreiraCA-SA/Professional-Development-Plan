# T-PLT-05-E — Expert Depth

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-e"></a>
#### T-PLT-05-E — Expert Depth

**Platform as a product organisation.** A platform team has a product manager function (even if shared), user research, a roadmap ranked by *how many developers hit a problem, how badly, how often*, a support model with response targets, and non-goals that protect focus. Treat internal users as customers who can decline: if use is mandatory you cannot learn whether the platform is good. Mandate only what safety requires (for example, production admission policy) and compete on experience for the rest.

**The thinnest viable platform.** Start with the smallest set that delivers a complete path, then add capabilities in response to measured stuck points. Overbuilt platforms fail by adding portals, operators and abstractions before basics (documented onboarding, a template that works, reliable CI) are reliable. Maintenance cost grows with every component; one maintainer cannot sustain many.

**Team topology and boundaries.** Define what the platform team provides as a *service* (self-service), a *capability* (enablement and consulting) or *collaboration* (temporary pairing). Align with cognitive-load thinking: the platform absorbs extraneous load (undifferentiated plumbing) so stream-aligned teams focus on their domain. Define explicit interaction modes and revisit them as maturity changes.

**Architecture defence.** A defence is a walkthrough followed by challenge by someone who has read your records. You are judged on *fidelity between claims and evidence* and on *trade-off reasoning*, not on how impressive the stack is. Keep a claims ledger with status values *Proven*, *Partial* and *Unproven*:

| Claim | Evidence | Status |
| --- | --- | --- |
| A stranger can create and deploy a service without help | Acceptance record | Proven (n = 1) |
| Artefacts are traceable to a commit | Verification output | Proven for CI-built images |
| Pod loss does not lose data | Drill timeline | Proven (practice cluster, single replica) |
| Node or cluster loss is recoverable | — | Unproven |
| The platform is secure | Policy and access transcripts | Partial — see limitations |

Claiming more than the ledger supports is the cardinal sin. Rehearse with a peer who scores *evidence for each answer, honesty about limits, named trade-offs* and *consistency with the decision records*.

**Questions a reviewer will ask**

1. Why this runtime rather than the alternative, and what would change your mind?
2. What does provenance prove, and what can a compromised build system still do?
3. Who can change production-shaped state, by what path, and where is that enforced?
4. A developer needs a database tomorrow — what happens, and who waits?
5. Where was your recovery-point target measured, and what if the backup job silently fails?
6. What does your status command *not* tell a developer?
7. What happens when the golden path is wrong for a team?
8. What did you decide not to build, and why was that right?
9. How much of this can a single maintainer sustain?

**Failure catalogue (organisational)**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Portal-first platform | Interface built before the path works | Trial before tooling; the decision test "would this remove an observed stuck point?" |
| Ticket queue with extra steps | Human gates for routine work | Automate; keep only designed, time-boxed human gates |
| Mandated mediocrity | Forced adoption of a poor path | Voluntary adoption signals; fast iteration |
| Unowned platform | Maintainer leaves | Documentation, runbooks, bus factor ≥ 2 |
| Overclaiming | Slides exceed evidence | Claims ledger reviewed by someone else |
| Silent gaps | Limitations discovered in incidents | Register maintained continuously |

**Mentoring prompts.** How would you decide whether your organisation needs a portal? Draft the three non-goals that would protect your platform from becoming a general-purpose PaaS. Which claim in your own ledger is weakest, and what is the cheapest experiment that would upgrade it?

---

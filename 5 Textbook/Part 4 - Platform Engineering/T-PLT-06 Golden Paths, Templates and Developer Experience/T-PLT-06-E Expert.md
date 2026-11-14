# T-PLT-06-E — Expert Depth

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-e"></a>
#### T-PLT-06-E — Expert Depth

**Running an independent trial properly.** *Who qualifies:* an engineer who has never used the platform and whom you do not coach; with prior knowledge of the underlying tools (Git, containers) but not your system. Prior exposure makes the result invalid.

*Setup the day before:* clean accounts, tool installs described as in the docs, access granted by the documented route, a planted safe failure for the investigation task, a recording method (with consent), and an author-only failure card (injection command, expected symptoms, expected diagnosis, expected recovery).

*Task cards:* four short tasks — create a service, make and promote a change, investigate a planted failure and recover, then answer a comprehension check. No hints on the cards.

*Observer rules — the hardest part:*

1. Say nothing except scripted prompts (start, end, "please think aloud").
2. If asked a question: "I can't help — what do the docs say?" and log it as a stuck point. If you then answer, it is an I2.
3. Never touch their keyboard.
4. Record timestamps as you go; do not reconstruct afterwards.
5. If a participant is blocked for more than fifteen minutes on a step, you may end the task as *FAIL (blocked)* — a valid, valuable result. Do not rescue and call it a pass.
6. Run the acceptance checks yourself rather than accepting the participant's word: service in the catalogue, status healthy, promotion recorded, recovery traceable to a pull request.
7. Debrief with three questions — what was most confusing, what would you remove, would you use it voluntarily — and capture verbatim quotes with consent.

*Results:*

| Result | Meaning | Action |
| --- | --- | --- |
| PASS | All tasks complete; no I2 or I3 interventions; findings recorded | Triage stuck points anyway |
| FAIL (intervention) | Undocumented help was needed | Convert each I2/I3 into a doc or product fix; recruit a *new* participant |
| FAIL (blocked) | Participant could not proceed | Same; the stuck point is the finding |
| INVALID | Prior platform knowledge or leaked author context | Discard the evidence and record why |

Use a *new* participant after a failure: a returning participant has learned the answers and you would measure recall. They may return later for a labelled "second service" speed measurement.

**Honest statistics.** With one or two participants you can find *problems*, not estimate *rates*. Report counts and quotes, not percentages that imply precision. An LLM given only the docs and a terminal can expose ambiguous steps quickly; label it an *automated docs probe — not a trial* and never use it to satisfy a pass standard.

**Turning findings into changes.** Convert each stuck point into a ranked backlog item with a source, an owner and a verification step; fix at least one severe finding and re-verify; keep the metric definitions fixed after the first trial (changes are logged) to avoid reinterpreting results.

**Template architecture at scale.** Versioned template sources, generated-service stamps (`golden path vN`) that allow measuring who is behind, automated upgrade pull requests for generated services, compatibility rules for the shared workflows (additive changes, deprecation windows), and golden-image or base-manifest releases with canary adoption. Avoid the "copy and diverge" trap by keeping shared logic referenced, not copied.

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Template rot | Not generated in CI | Scheduled generation and deployment tests |
| Docs drift | Steps change, docs do not | Docs tested in trials and by automated probes |
| Status that lies | Healthy reported for unpromoted or stale services | Explicit `UNKNOWN`; checks for freshness and drift |
| Author-blindness | The builder cannot see stuck points | Independent trials; rehearsal runs labelled as such |
| Path ossification | The golden path blocks innovation | Escape hatch, deviation process, periodic review |
| Support overload | Repeated questions | Convert to docs or fixes weekly; measure by category |

**Developer experience beyond the platform.** Fast local feedback (build and test times), reliable CI, short review latency, clear ownership, low-friction access, trustworthy environments, and psychologically safe incident culture. Use frameworks such as DORA metrics (deployment frequency, lead time, change failure rate, time to restore) and developer-experience surveys as *signals*, not targets — optimising a metric directly invites gaming. Combine quantitative signals with qualitative research.

**Mentoring prompts.** An I2 intervention occurred because the participant could not find the access request page. What are all the changes you could make, and which first? How do you tell the difference between a platform problem and a participant problem? How would you decide to retire part of the golden path?

---

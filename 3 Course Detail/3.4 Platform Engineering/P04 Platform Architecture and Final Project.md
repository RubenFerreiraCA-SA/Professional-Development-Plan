# P04 — Platform Architecture and Final Project

| | Details |
| --- | --- |
| **Estimated study time** | 40–50 hours |
| **Prerequisites** | [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) trial evidence (or scheduled trial with documented readiness). In-scope DevOps/Cloud Harbour path substantially complete. |

**Purpose:** Integrate prior capabilities into one demonstrable Internal Developer Platform; defend architecture; complete the [programme Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md) demonstration.

## Module overview

P04 is not a broad essay about platforms. It is the **integrated technical defence**: one system where create → review → trusted build → self-service deploy → health/failure/recovery → independent acceptance can be shown end to end. Include at least one **stateful** failure/recovery scenario (C03’s primary app path may have been intentionally stateless).

## Learning outcomes

1. Trace a service from template through immutable artifact to runtime with provenance evidence.  
2. Demonstrate self-service deployment into an approved environment under identity and policy controls.  
3. Show health, failure injection/recovery and runbook use with telemetry.  
4. Execute (or re-run) independent developer acceptance and record findings.  
5. Defend trade-offs from ADRs; maintain a claims ledger (Proven / Partial / Unproven).

## Learning activities

| Activity | Core learning and practical work | Hours |
| --- | --- | ---: |
| 1 | Platform architecture patterns, service boundaries, self-service API/CLI contracts, ADR set | 8–10 |
| 2 | Golden-path integration: templates, automation, provisioning and deployment workflows | 8–10 |
| 3 | Platform controls: policy-as-code, secrets, observability, SLOs, cost governance | 8–10 |
| 4 | Reliability: failure injection, **stateful** recovery, monitoring, user-testing follow-ups | 8–10 |
| 5 | Final implementation polish, evidence pack, demonstration rehearsal and PDP reflection | 8–10 |
| **Total** | | **40–50** |

## Minimum integrated outcome

| Capability | Pass when… |
| --- | --- |
| Developer creates a service | Approved template or golden path |
| Reviewed change and trusted build | Tests, provenance, immutable artifact |
| Self-service deployment | Approved environment, identity, policy |
| Health, failure and recovery | Telemetry, runbooks, evidence (include stateful scenario) |
| Independent developer acceptance | No author assistance; findings recorded |

## Assessment and completion criteria

**Acceptance (Competent):** Satisfy every **Required** [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) final-demonstration item for your in-scope pathway; defend trade-offs from ADRs; do not tick Unproven claims as Proven.

**Evidence:** End-to-end demo notes, decision set, claims ledger, PDP reflection, stateful recovery record.

## Certifications (optional)

Architecture/defence skills are demonstrated here; external certs remain optional and separate.

**Textbook:** [Chapter 4 — Platform Architecture and Final Project](../../4%20Study%20Materials/4.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md)

**Previous:** [P03](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) · **Syllabus:** [P00](P00%20Platform%20Syllabus.md)

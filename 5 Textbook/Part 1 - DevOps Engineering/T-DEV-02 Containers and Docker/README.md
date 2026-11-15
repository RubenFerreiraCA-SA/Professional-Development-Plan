# T-DEV-02 — Containers and Docker

*Part 1 — DevOps Engineering*


A container is a process with a restricted view of the system, not a small virtual machine. Understanding that one sentence explains packaging, security, resource limits, signal handling and many production failures.

## Levels


- [Beginner Foundations](T-DEV-02-B%20Beginner.md#t-dev-02-b) — containers versus VMs and images, layers, registries, a first annotated Dockerfile, build/run/stop/logs, ports, networks, volumes, safe inspection and removal, common mistakes.
- [Intermediate Practice](T-DEV-02-I%20Intermediate.md#t-dev-02-i) — PID 1 and signals, multi-stage builds, Compose, bind mounts versus volumes, DNS between containers, environment variables, health versus readiness, a troubleshooting routine, caching, build failures, reproducibility.
- [Professional Engineering](T-DEV-02-P%20Professional.md#t-dev-02-p) — non-root and hardened runtime, minimal images, digest pinning, vulnerability triage, SBOM, provenance and signing, registry controls, workload limits, production diagnostics, the runtime contract.
- [Expert Depth](T-DEV-02-E%20Expert.md#t-dev-02-e) — namespaces, cgroups and capabilities on the host, rootless operation, seccomp and the limits of isolation, multi-platform images, supply-chain attacks, performance and footprint, orchestrators, expert trade-offs.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.

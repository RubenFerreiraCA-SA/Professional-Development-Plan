# Glossary

| Term | Definition |
| --- | --- |
| ADR | Architecture decision record: a short document capturing a decision, alternatives, consequences, evidence and revisit trigger. |
| Admission control | Checks and mutations applied by the Kubernetes API server to objects after authentication and authorisation. |
| Agent (AI) | A loop in which a model proposes tool calls that application code validates and executes, feeding results back. |
| Allow-list | A list of explicitly permitted names or actions; everything else is denied. |
| Artefact | A build output such as a container image or package. |
| Attestation | A signed statement about an artefact, for example how and from what it was built. |
| Availability zone (AZ) | An isolated location within a cloud region, made of one or more datacentres. |
| Blast radius | The extent of damage caused by a failure or compromise. |
| Branch | A movable name pointing at a commit. |
| Break-glass | Emergency access that bypasses normal controls, strictly logged and reviewed. |
| Canary | A release technique that exposes a change to a small share of traffic first. |
| cgroup | A Linux kernel feature that limits and accounts for process resource use. |
| CI/CD | Continuous integration and continuous delivery or deployment: automated validation and release of changes. |
| CIDR | Notation for IP address ranges, for example `10.0.0.0/16`. |
| Cognitive load | The mental effort required to perform a task; platforms aim to reduce the extraneous part. |
| Commit | A recorded snapshot in Git history with author, message and parents. |
| Context window | The maximum number of tokens a model can consider in one request. |
| Controller | A control loop that drives actual state toward desired state. |
| Counter, gauge, histogram | Metric types: monotonically increasing, up-and-down, and distribution of values. |
| Cardinality | The number of distinct label or tag combinations for a metric; high cardinality drives cost. |
| DaemonSet | A Kubernetes workload that runs one Pod per node. |
| Default deny | A policy stance in which traffic or actions are blocked unless explicitly allowed. |
| Deployment (Kubernetes) | A controller managing ReplicaSets for rolling updates and rollback of stateless workloads. |
| Digest | A content-derived identifier of an image (`sha256:…`); immutable, unlike a tag. |
| Drift | A difference between desired state and live state. |
| Embedding | A numeric vector representing text so that similar meanings are close together. |
| Error budget | The amount of unreliability an SLO permits over a window. |
| Evaluation (AI) | A fixed set of cases with expectations run after every change to measure behaviour. |
| Golden path | The opinionated, supported, easiest way to perform a common engineering job. |
| GitOps | An operating model where Git holds desired state and a controller reconciles reality toward it. |
| Grounding | Conditioning model answers on supplied, trusted text and requiring them to stay within it. |
| Hallucination | Fluent output that is unsupported or false. |
| HPA | Horizontal Pod Autoscaler: scales replica counts on observed metrics. |
| IaC | Infrastructure as code: defining infrastructure in versioned, reviewable text. |
| IAM | Identity and access management: the system of principals, policies and roles controlling who may do what. |
| Idempotent | An operation that has the same effect whether applied once or many times. |
| Image | An immutable layered filesystem plus configuration used to start containers. |
| Index (Git) | The staging area holding the next candidate snapshot. |
| Intervention (trial) | Any information given to a participant that is not in the written documentation. |
| Kill switch | A single, tested action that disables a feature or capability. |
| Least privilege | Giving identities only the permissions needed for their responsibilities. |
| LLM | Large language model: a model that predicts text and can follow instructions. |
| LLMOps | Operating an LLM-based feature: versioning, serving, monitoring, limiting and disabling it. |
| Merge base | The most recent common ancestor of two branches. |
| Module (Terraform) | A reusable bundle of configuration with inputs and outputs. |
| Namespace (Kubernetes) | A scope for names, quotas and access rules within a cluster. |
| Namespace (Linux) | A kernel feature that gives a process an isolated view of system resources. |
| NetworkPolicy | A Kubernetes object restricting Pod traffic, effective only when the network plugin enforces it. |
| Observability | The ability to understand a system's internal state from its external outputs. |
| OIDC | OpenID Connect: an identity protocol used, for example, to give CI runs short-lived cloud credentials. |
| OpenTelemetry | A vendor-neutral standard and toolkit for metrics, logs and traces. |
| PDB | PodDisruptionBudget: limits voluntary evictions of a set of Pods. |
| Plan (Terraform) | A computed set of changes between configuration, state and reality. |
| Pod | The smallest schedulable Kubernetes unit: containers sharing network and volumes. |
| Probe | A health check run by the kubelet: startup, readiness or liveness. |
| Prompt injection | Text in input or data that tries to make a model ignore its instructions. |
| Promotion | Moving a known artefact to an environment by changing a pointer, without rebuilding. |
| Provenance | Verifiable metadata linking an artefact to its source and build process. |
| RAG | Retrieval-augmented generation: retrieve relevant text, then generate an answer from it. |
| RBAC | Role-based access control: permissions granted through roles bound to subjects. |
| Readiness | Whether a workload should currently receive traffic. |
| Reconciliation | A loop that compares desired and live state and acts to converge them. |
| Reflog | A local record of where Git references pointed over time. |
| Remote | A named destination for fetching and pushing Git history. |
| RPO / RTO | Recovery point objective (tolerable data loss) and recovery time objective (tolerable downtime). |
| SBOM | Software bill of materials: an inventory of components in an artefact. |
| Service (Kubernetes) | A stable address and DNS name load-balancing across ready Pods. |
| SLI / SLO | Service level indicator (a measured ratio) and objective (a target for it over a window). |
| Shared responsibility | The division of security and operational duties between cloud provider and customer. |
| State (Terraform) | Terraform's record mapping configuration to real objects; privileged data. |
| StatefulSet | A Kubernetes workload with stable identity and per-Pod storage. |
| Supply chain | The sequence of identities, dependencies, processes and artefacts from source to deployed software. |
| Tag (container) | A mutable name for an image; contrast with digest. |
| Token (LLM) | A chunk of text used as the unit of model input, output, limits and cost. |
| Trace / span | A request's end-to-end path and its constituent timed operations. |
| Trust boundary | A line across which data or code moves between different levels of trust. |
| VPC | Virtual private cloud: an isolated, user-defined network in a cloud provider. |
| Workload identity | A short-lived identity given to a running workload rather than a person. |
| Burn rate | How quickly an error budget is being consumed relative to the SLO window. |
| Field manager | In Kubernetes server-side apply, the recorded owner of a field; conflicts arise when managers disagree. |
| Gray failure | A degraded mode that is neither fully healthy nor fully down, often hard for coarse monitoring to detect. |
| Head / tail sampling | Trace sampling at the start of a request versus after the outcome is known. |
| Landing zone | A governed baseline of accounts, identity, networking and logging from which cloud workloads are launched. |
| Partial clone / sparse checkout | Git techniques that fetch or materialise only part of a large repository. |
| Ruleset | Hosting-provider policies (often as code) that enforce branch protections and related controls. |
| Saga | A multi-step workflow with compensating actions when a later step fails. |
| Wilson interval | A confidence interval for a proportion that behaves better than a naive normal approximation on small samples. |

---

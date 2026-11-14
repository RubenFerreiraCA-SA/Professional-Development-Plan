# T-CLD-04-P — Professional Engineering

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-p"></a>
#### T-CLD-04-P — Professional Engineering

**Least privilege in practice.**

- Start from zero and add actions you observe being needed (access advisor and audit logs show used permissions); replace wildcards with specific resources.
- Use *permission boundaries* to cap what delegated administrators can grant.
- Use *conditions*: source IP or VPC endpoint, MFA present, resource tags, time.
- Prefer roles with short-lived credentials; federate human access through single sign-on.
- Separate roles for *plan*, *apply*, *read-only audit* and *break-glass*.
- Review access regularly; remove unused principals and keys.

**Policy evaluation, simplified.** A request is allowed only if some applicable policy allows it, no applicable policy denies it, and any boundaries or organisation-level policies also permit it. Resource policies (for example on a storage bucket) can grant cross-account access independently of identity policies. When debugging `AccessDenied`, check in order: identity policy, permission boundary, session policy, organisation policy, resource policy, then conditions.

**Network security design.**

| Layer | Control |
| --- | --- |
| Perimeter | Load balancer with TLS, web application firewall for HTTP workloads |
| Subnet | Public only for edge components; private for workloads and data |
| Instance or task | Security groups referencing other groups, not wide CIDR ranges |
| Egress | NAT with restrictions or private endpoints to managed services |
| Data | Encryption at rest and in transit, private endpoints, no public databases |
| Observability | Flow logs and load-balancer logs to a protected location |

Using VPC endpoints for object storage, container registries and secrets keeps traffic off the internet and can reduce NAT charges. Compare endpoint costs with NAT costs for your volume.

**Cost controls in operation.** Budgets with actions, anomaly detection, tag enforcement through policy, scheduled shutdown of non-production, rightsizing reviews and storage lifecycle rules. Explicitly estimate: load balancer hours, compute hours and memory, NAT hours plus data processing, data transfer and logs. A common surprise: log ingestion and cross-AZ traffic. Make teardown documented and tested.

**Evidence of control.** Keep these artefacts: identity baseline with allowed and denied evidence; network baseline with identifiers taken from infrastructure outputs; services map; budget screenshot or export; ADR. A claim without evidence is a risk; "pending apply" is an honest status.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Demo or operate daily | Limited operator role with MFA | Standing administrator |
| Allow a service to call an API | Task or instance role with specific actions | Long-lived access keys in environment variables |
| Expose a service | Load balancer SG open; app SG only from the load balancer | `0.0.0.0/0` on application or SSH |
| Debug AccessDenied | Policy simulator, identity then boundary then resource | Adding `*` until it works |
| Keep a bill small | Budget first, idle policy, teardown | Always-on NAT in a lab |

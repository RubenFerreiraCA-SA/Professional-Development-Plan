# T-CLD-04 — AWS Identity, Networking and Cost Controls

*Part 2 — Cloud Engineering*


This topic applies the cloud foundations to Amazon Web Services: identity and access management (IAM), the virtual private cloud (VPC) edge for a service, workload identity, audit logging, guardrails and cost controls. The concepts carry over to other providers under different names. The central distinction of the chapter is that **permission and reachability are different questions**: a caller can be allowed but unable to reach a service, or able to reach it and refused.

## Levels


- [Beginner Foundations](T-CLD-04-B%20Beginner.md#t-cld-04-b) — accounts, Regions and shared responsibility, IAM vocabulary, ARNs, reading a policy, roles and temporary credentials, basic request evaluation, VPC, CIDR, subnets, route tables and security groups, permission versus reachability, budgets and tagging, common mistakes.
- [Intermediate Practice](T-CLD-04-I%20Intermediate.md#t-cld-04-i) — full policy evaluation layers and conditions, assuming roles across accounts, iterative least privilege and the simulator, workload roles, VPC routing and endpoints, security groups versus network ACLs, public and private subnets, tags and budgets, a layered troubleshooting routine.
- [Professional Engineering](T-CLD-04-P%20Professional.md#t-cld-04-p) — identity architecture and separation of duties, pipeline federation, cross-account patterns, segmentation, egress control, logging and audit, guardrails, cost modelling with break-even arithmetic, written policy decisions and evidence.
- [Expert Depth](T-CLD-04-E%20Expert.md#t-cld-04-e) — organisation boundaries and policy ceilings, escalation paths, trust chains and attribute-based access, multi-VPC and transit design, address planning, hybrid networking, enterprise cost allocation, exceptions, failure patterns and expert trade-offs.

All examples use a neutral `orders` service and placeholder account IDs; the chapter has no dependency on any other course material. Text tagged **[AWS-specific]** describes behaviour particular to this provider; text tagged **[Version-sensitive]** describes limits, defaults, prices, console labels or message wording that change over time and must be checked against current documentation. Outputs and figures marked *illustrative* show expected shapes and arithmetic, not measured results.

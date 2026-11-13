# D05 — Infrastructure as Code and Terraform

| | Details |
| --- | --- |
| **Estimated study time** | 42–60 hours |
| **Prerequisites** | [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md), [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md), working knowledge of networking, IAM and Linux. Access to an isolated cloud sandbox or a suitable lab environment. |

## Objective

Engineer **reproducible infrastructure that development teams can safely consume**. Learn Terraform as a platform delivery mechanism: state is protected, changes are reviewable, modules form stable interfaces and failure recovery is designed in from the start.

## Outcomes

1. Explain Terraform's provider model, dependency graph, drift, refresh, planning and resource lifecycle.
2. Protect and recover remote state, including locking, sensitive content and concurrent change.
3. Develop versioned, tested modules with explicit inputs, outputs, validation and upgrade paths.
4. Manage isolated environments and permission boundaries without copying infrastructure configuration indiscriminately.
5. Provision cloud networking, access control and container-hosting infrastructure with safe defaults.
6. Apply a gated plan-and-apply workflow with policy checks and auditable approval.
7. Diagnose drift, replacement, failed provisioning and recovery scenarios without destroying unrelated services.

## 1. Terraform architecture and change semantics

Design a small cloud environment for the application built in D03: private service/network boundary, controlled ingress, runtime environment, IAM and state backend.

Explore providers, pinned versions, resources, data sources, module boundaries, variables, outputs, locals and lifecycle meta-arguments. Explain when an implicit reference models a dependency correctly and when an explicit dependency is actually required.

```bash
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -out=tfplan
terraform show tfplan
```

**Do this in a sandbox.** Saved plan files and state can contain sensitive data; do not commit them or upload them to public artifacts. Keep the provider lockfile under source control and define an upgrade procedure.

**Exercise:** Identify a proposed resource replacement, document its blast radius, and design a migration or maintenance strategy. Explain why a previously reviewed plan may become invalid when the state or external environment changes.

## 2. Remote state, locking and drift

Treat state as a privileged, recoverable information store:

- Choose an access-controlled remote backend with locking where supported.
- Restrict state access by environment and execution identity; encrypt and back up state.
- Explain the limits of marking an output `sensitive`: values can still reside in state.
- Partition state by ownership and blast radius, rather than putting an entire organisation into one state file.
- Know when to use import blocks, `moved` blocks, explicit `terraform state` commands, and when not to.

**Failure drills:**

1. Make two competing changes in a disposable environment. Observe locking and safe resolution; never force-unlock a genuinely active operation.
2. Create benign out-of-band drift. Run a fresh plan, decide whether to reconcile, import or intentionally accept the difference, and justify the decision.
3. Simulate a failed apply or partial creation. Investigate actual provider resources and state before retrying. Demonstrate safe recovery from a backend version or snapshot, without overwriting live state blindly.

Keep a short incident log recording symptoms, root cause, decision and prevention.

## 3. Reusable modules and platform interfaces

Create reusable **network** and **application runtime** modules. A module is an API for other engineering teams, not merely a folder:

- Define required inputs, defaults, validation, outputs and example usage.
- Specify provider and Terraform version compatibility.
- Avoid hardcoded account IDs, broad permissions and environment-specific naming inside reusable modules.
- Version the module and document breaking changes, migrations and deprecation.
- Use `for_each`/dynamic blocks where the resulting interface remains understandable; avoid abstractions that obscure ownership.

**Testing strategy:** combine static validation with `terraform test` where appropriate, policy checks and at least one disposable integration deployment. Check that required defaults are secure and that a module can be upgraded without accidental replacement.

**Exercise:** Deploy two isolated environments using the same module versions and different inputs. Demonstrate that a change aimed at one environment does not alter the other.

## 4. Cloud infrastructure, IAM and network security

Provision only the components required by the project's current scope:

- Segmented network/subnets and controlled ingress/egress.
- A container runtime or compute environment appropriate to the provider.
- Scoped workload identity, least-privilege execution roles and separation of operator access.
- Service configuration and secrets references without persisting credentials in the repository.
- DNS, health checks, logging and cost labels/alerts as supported.

**Architecture review:** draw the trust boundaries and explain what an attacker could access if the application workload were compromised. Identify where permissions and network policies limit lateral movement.

Measure resources created, forecast recurring charges, configure budget protection and document teardown. **Destroy only sandbox resources that you own**, after inspecting the plan.

## 5. Pipeline integration and policy controls

Reuse the trusted CI patterns developed in D04:

1. Run formatting, validation, module tests, security/policy checks and a speculative plan on a pull/merge request.
2. Summarise proposed resource changes, replacements, cost implications and sensitive operations without exposing secret values.
3. Apply only from an approved, protected context using short-lived credentials where available.
4. Re-plan under the authorised context when necessary; never apply an outdated plan after state has materially changed.
5. Record the execution identity, source revision, environment, plan outcome and apply result.
6. Define policy checks for internet exposure, privilege breadth, required tags and protected resource deletion.

**Threat drill:** model a malicious or mistaken infrastructure PR that attempts to grant public access or excessive IAM permissions. Demonstrate that the review process blocks it or explicitly document the policy-enforcement gap.

## Practical Assessment — infrastructure platform contract

Deliver a reusable, documented infrastructure offering for the Final Project.

**Evidence required:**

- Two isolated environments using versioned modules and explicit variables.
- A secured remote backend, visible locking behaviour and a recovery/backup decision.
- Reviewable CI plan checks, an approved apply and a recorded change trace.
- A functioning application endpoint or runtime connected to appropriate network and IAM controls.
- A drift or failure exercise with documented detection and recovery.
- A short ADR covering module boundaries, state isolation, costs, risks and upgrade strategy.

**Acceptance:** A second engineer can provision, review, update and safely tear down **one** environment without compromising the other or requiring undocumented credentials. Infrastructure code is not considered complete merely because `terraform apply` succeeded.

## Further learning

- [Terraform — Documentation](https://developer.hashicorp.com/terraform/docs)
- [Terraform — State](https://developer.hashicorp.com/terraform/language/state)
- [Terraform — Modules](https://developer.hashicorp.com/terraform/language/modules)
- [Terraform — Testing](https://developer.hashicorp.com/terraform/language/tests)
- [OWASP — Infrastructure as Code Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html)

**Previous:** [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md) · **Next:** [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md)

# T-PLT-03-E — Expert Depth

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-e"></a>
#### T-PLT-03-E — Expert Depth

**Threat model for a cluster.** Assets: workloads and data, credentials, the control plane, the supply chain. Adversaries: external attackers exploiting an application, malicious insiders or tenants, compromised CI, malicious dependencies. Typical chain: remote code execution in a Pod → read the ServiceAccount token or metadata credentials → query the API or cloud → escalate through over-broad RBAC or a privileged Pod → reach nodes and other tenants. Each defence breaks a link: input handling, non-root and read-only filesystems, token automount off, metadata endpoint blocked, least-privilege RBAC, admission policy, network policy, node hardening and runtime detection.

**Escalation analysis in depth.** The permission to create Pods in a namespace is effectively access to every Secret and ServiceAccount there. Permission to create privileged Pods or mount `hostPath` is node-level access. Permission to modify admission webhooks or policies is control over all future objects. Permission to create tokens for powerful ServiceAccounts or to impersonate is delegation of those identities. Walk each role through "what is the worst thing this can do transitively" and use graph-based analysis tools in CI.

**Policy engine design at scale.** Policies are code: version them, test them, review them, roll them out progressively. Consider performance and availability of webhook-based admission: a failing webhook with `failurePolicy: Fail` can block all changes (including recovery), whereas `Ignore` silently disables enforcement. Exclude the policy engine's own namespace and critical system namespaces carefully, keep break-glass procedures, monitor webhook latency and errors, and prefer in-process mechanisms (CEL policies) for simple rules to reduce failure modes.

**Runtime security.** Admission is static; attackers act at runtime. Complement with runtime detection (syscall and network anomaly detection through eBPF-based tools), read-only filesystems, minimal images, seccomp and AppArmor or SELinux profiles, and alerting on suspicious behaviours (shell in a container, unexpected outbound connections, credential file reads). Define response playbooks: isolate the Pod with a network policy, capture evidence, rotate exposed credentials, replace the workload.

**Isolation strength.** Containers share a kernel; for untrusted workloads consider sandboxed runtimes (user-space kernels or micro-VMs), dedicated node pools with taints, and separate clusters. Weigh performance overhead, compatibility and operational cost against risk.

**Identity and zero trust.** Workload identity (short-lived, attested identities per Pod), mutual TLS between services, authorisation policies at the mesh or application layer, and no long-lived static credentials. A service mesh adds these capabilities and costs: complexity, resource overhead, new failure modes and upgrade burden. Adopt when requirements justify it.

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Policy engine outage blocks recovery | `failurePolicy: Fail` with a down webhook | HA deployment, exclusions, break-glass, simple CEL policies |
| Over-permissive operator | Operator granted cluster-admin | Review operator RBAC, namespace scope, vendor assessment |
| Secrets in etcd backups | Backups unencrypted | Encrypt, restrict, test restore |
| Stale exceptions | Exceptions never expire | Expiry and quarterly review |
| Token theft | Long-lived tokens, automount default | Bounded tokens, automount off, metadata blocking |
| Escape via privileged tooling | CI or debug Pods run privileged | Separate debug procedures, ephemeral containers with RBAC and policy |

**Mentoring prompts.** Why is "can create Pods" nearly equivalent to "can read all Secrets in the namespace"? How would you roll out a new mandatory policy to a hundred teams without causing an incident? What are the trade-offs of fail-open versus fail-closed admission, and how do you mitigate each?

---

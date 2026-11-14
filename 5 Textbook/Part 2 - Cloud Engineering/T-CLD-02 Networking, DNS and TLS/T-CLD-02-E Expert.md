# T-CLD-02-E — Expert Depth

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-e"></a>
#### T-CLD-02-E — Expert Depth

**Beyond the basics of name resolution.** Resolution has many caches: application, operating system, node-local, recursive. Negative caching means a mistaken lookup can persist. Split-horizon DNS returns different answers inside and outside a network; service meshes and container platforms add their own resolvers with search-path behaviour (`ndots`) that can multiply queries and produce surprising failures. Resolver timeouts are a classic cause of tail latency.

**Reading packets.** When logs and counters are insufficient, capture traffic: `tcpdump -i any -nn port 443 -w out.pcap`, then inspect with Wireshark. Look for retransmissions (loss), `RST` (refusal or abort), zero windows (receiver overload), long gaps before the first `SYN-ACK` (path or filter) and handshake alerts (TLS). Capture is sensitive: handle files as confidential, and prefer metadata unless you must see payloads.

**TLS beyond defaults.** Protocol versions and cipher suites should follow current guidance. Mutual TLS authenticates both sides and underpins zero-trust service-to-service designs; certificate rotation at scale needs automation and short lifetimes. Revocation is weak in practice; short-lived certificates reduce reliance on it. Pinning reduces CA trust at the cost of operational fragility. SNI-based routing, ALPN and session resumption influence behaviour behind proxies.

**Failure modes at scale**

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Connection-tracking exhaustion | Many short flows through NAT | Larger tables, pooling, keep-alives |
| Ephemeral-port exhaustion | Outbound connections to one destination | Connection reuse, more source addresses |
| MTU black holes | Fragmentation blocked, path MTU discovery broken | Clamp MSS, consistent MTU |
| DNS amplification of load | Chatty clients, low TTLs, long search paths | Node-local caches, fewer lookups |
| Asymmetric routing | Return path differs and stateful filters drop it | Consistent route design |
| Certificate expiry outage | No monitoring or automation | Expiry alerts, automated renewal |
| Retry storms | Clients retry simultaneously after a blip | Backoff with jitter, retry budgets |

**Designing for partial failure.** Timeouts on every network call; bounded retries with exponential backoff and jitter; idempotent operations so retries are safe; circuit breakers and load shedding to protect dependencies; health checks that distinguish a dead instance from a degraded dependency.

**Hypothesis ranking: "works from my laptop, times out from production".** Start from the hypotheses, then pick the cheapest experiment that splits them.

| Hypothesis | Experiment from the production host (or a debug Pod) | Eliminates / confirms |
| --- | --- | --- |
| DNS resolves differently (split-horizon or stale cache) | `dig +short name @<resolver>` versus `getent hosts name`; compare with laptop | Different answers confirm; same answers eliminate DNS |
| Route or security-group/firewall drop | `nc -vz -w 3 <ip> 443`; `ip route get <ip>` | Timeout with a correct route points at a filter; refusal means the host is reachable |
| MTU black hole (small requests work, large ones hang) | `ping -M do -s 1472 <ip>` stepping the size down; `curl` with a large POST | Failure above a size confirms; hang after the TLS ClientHello is typical |
| Ephemeral-port or conntrack exhaustion | `ss -s`; `sysctl net.netfilter.nf_conntrack_count`; kernel log | Counts near limits confirm; intermittent failures at peak |
| TLS or SNI mismatch | `openssl s_client -connect <ip>:443 -servername name -brief` | Alert or wrong certificate confirms |
| Egress proxy or policy only applied in production | `env \| grep -i proxy`; compare `curl -v` output | Different path confirms |

Order the experiments by cost and by how much of the hypothesis space each removes. Record what you did *and what it ruled out*, not only what you found.

**`ndots` amplification, worked.** With `ndots:5` and search domains `ns.svc.cluster.local svc.cluster.local cluster.local`, resolving `api.example.com` (two dots, fewer than five) tries each search suffix first, in both A and AAAA forms, before the real name:

```text
api.example.com.ns.svc.cluster.local     NXDOMAIN
api.example.com.svc.cluster.local        NXDOMAIN
api.example.com.cluster.local            NXDOMAIN
api.example.com.                         answer      # 4 names x 2 record types = up to 8 queries
```

A client making 1,000 lookups per second can become 8,000 queries per second against the resolver, with timeouts appearing as application latency. Mitigations: use fully-qualified names with a trailing dot, lower `ndots` where appropriate, run a node-local cache, and reuse connections.

**Reading a capture: signatures to recognise.**

```bash
tcpdump -i any -nn -s 96 'host 10.0.2.15 and port 443' -w case.pcap
tcpdump -nn -r case.pcap 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'
```

| What you see | Meaning | Next step |
| --- | --- | --- |
| `SYN` repeated at 1 s, 2 s, 4 s, no `SYN-ACK` | Packets dropped, or reply filtered; the path or a filter is at fault | Check security groups, ACLs and routes; capture at the other end |
| `SYN` then immediate `RST,ACK` | Host reached, nothing listening on that port | Check the process, port, and bind address |
| `SYN-ACK` arrives but client's ACK never seen on server | Asymmetric routing or stateful filter on the return path | Compare captures at both ends |
| Many retransmissions of the same segment | Loss on the path | Check interface errors, congestion, MTU |
| Window size 0 | Receiver cannot keep up | Look at the application reading the socket |
| TLS `Alert (Level: Fatal, Description: …)` | Handshake rejected by a peer | Read the alert type: `unknown_ca`, `certificate_expired`, `handshake_failure` |

Compare a capture from both ends. If the sender shows a packet leaving and the receiver never sees it, the loss is in between. Keep packet files confidential and delete them when the case closes.

**Trade-offs: mTLS, short-lived certificates, pinning.**

| Option | Gain | Operational cost | Typical failure |
| --- | --- | --- | --- |
| Mutual TLS | Both sides authenticated; identity-based policy | Issuance and rotation for every workload; debugging two-sided handshakes | A rotation misses a client and calls fail with `bad_certificate` |
| Short-lived certificates (hours to days) | Less reliance on weak revocation; small exposure window | Needs reliable automation and a highly available issuer | Issuer outage becomes a fleet-wide outage when certificates expire |
| Pinning | Resists mis-issuance by other authorities | Brittle; any legitimate key change breaks clients | Forced emergency key change locks out clients without an update |

Design for the *failure mode of the control*: monitor days-to-expiry for every certificate and for the issuer's own chain, overlap validity periods during rotation, and test rotation in staging with a deliberately short lifetime. A CA certificate that expires without a plan takes down everything that trusts it, so give CAs long runway, an inventory of dependents and a rehearsed replacement.

**Partial failure design with numbers.** Suppose a dependency usually answers in 50 ms and degrades to 5 s. A caller with a 30 s timeout and three retries holds a thread for up to two minutes per request; with 200 threads the caller is exhausted within seconds, and callers of *that* service then fail. Defences work together: a per-call timeout close to p99 (for example 300 ms), at most one retry with jittered exponential backoff (`sleep = random(0, base × 2^attempt)`), a retry budget of about 10% of requests, a circuit breaker that opens after repeated failures, and a fallback or fast 503. Retries are safe only for idempotent operations; use idempotency keys for payments or order creation.

**Why `curl -k` misleads.** It disables validation, so the one thing you are testing (the certificate chain) is skipped. Use `openssl s_client -showcerts`, `curl --cacert`, and `curl -v` to read the verification error, and compare dates, names (`subjectAltName`) and chains.

**Incident analysis structure for a network failure.** Timeline with timestamps and data sources; the hypotheses considered and how each was ruled out; the actual mechanism; the detection gap (why no alert fired first); mitigations with owners and dates.

**Mentoring prompts.** A service works from your laptop and times out from production; list the first five experiments you would run and what each would rule out. Why is `curl -k` usually the wrong tool for investigating a certificate problem? How would you design certificate rotation so that an expiring CA does not take the company offline?

---

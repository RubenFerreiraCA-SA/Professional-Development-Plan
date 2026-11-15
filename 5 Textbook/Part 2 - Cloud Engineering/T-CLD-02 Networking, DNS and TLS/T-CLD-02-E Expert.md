# T-CLD-02-E — Expert Depth

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-e"></a>
#### T-CLD-02-E — Expert Depth

## Why this matters

Experts are paid for the failures that do not match the runbook: a path that works for 99% of connections, a certificate that is valid for most clients, a failover that technically happens and still takes the service down, a migration that succeeds in every test and fails for the one customer who runs a ten-year-old resolver. These failures share a property: they are **partial**. Something works, something does not, and the boundary between them is the clue.

This section assumes the Beginner, Intermediate and Professional material. It covers hybrid and multi-region connectivity, zero-trust service identity, traffic engineering, partial-failure design, DNS and TLS incidents, the tension between security controls and availability, and how to migrate networks, names and certificates without an outage. Case studies are **composite and illustrative**: they show shapes of real incidents, not any specific organisation's records.

## Beyond the basics of name resolution

Resolution has many caches: application, operating system, node-local, recursive. **Negative caching** means a mistaken lookup can persist. **Split-horizon DNS** returns different answers inside and outside a network; service meshes and container platforms add their own resolvers with search-path behaviour (`ndots`) that can multiply queries and produce surprising failures. Resolver timeouts are a classic cause of tail latency.

**Transport details that matter.** DNS uses UDP first and falls back to TCP when a response is truncated or when the client wants a larger answer. Modern guidance keeps UDP payloads at or below roughly 1,232 bytes to avoid IP fragmentation, so large responses (many records, DNSSEC signatures) fall back to TCP; networks that block DNS over TCP, or middleboxes that drop fragments, then cause failures that appear only for certain names. A resolver that waits for a full timeout (often several seconds) before retrying turns one dropped UDP packet into seconds of latency.

**DNSSEC** signs zone data so validating resolvers can detect forgery. Its failure mode is availability: if signatures expire, or a `DS` record at the parent no longer matches the zone's key (a typical outcome of a provider migration), validating resolvers return `SERVFAIL` and the name vanishes for the users behind them, while non-validating resolvers still answer. The diagnostic is to compare:

```bash
dig orders.example.com A +dnssec @validating-resolver      # SERVFAIL?
dig orders.example.com A +cd @validating-resolver          # +cd disables validation: answer returns?
dig DS example.com +short ; dig DNSKEY example.com +short  # do parent and child agree?
```

If `+cd` makes the answer reappear, validation, not reachability, is failing.

**Happy Eyeballs.** Clients with both IPv4 and IPv6 addresses race connection attempts (RFC 8305 style), preferring IPv6 but falling back within a few hundred milliseconds. A broken IPv6 path therefore appears as occasional extra latency rather than failure. If you publish `AAAA` records, you must monitor IPv6 as a first-class path.

**Runtime caching.** Some runtimes resolve a name once per process or per pool and never again, so DNS-based failover is invisible to long-lived connections. Know your runtime's behaviour (for example, a JVM's default positive-cache duration and the way it can differ when a security manager is present), set it explicitly, and make connection pools recycle connections periodically.

## Reading packets

When logs and counters are insufficient, capture traffic: `tcpdump -i any -nn port 443 -w out.pcap`, then inspect with Wireshark. Look for retransmissions (loss), `RST` (refusal or abort), zero windows (receiver overload), long gaps before the first `SYN-ACK` (path or filter) and handshake alerts (TLS). Capture is sensitive: handle files as confidential, and prefer metadata unless you must see payloads.

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
| Handshake completes, then `RST` after idle | A middlebox (NAT, balancer) expired the flow | Compare idle timeout to keep-alive interval |
| Small packets pass; large ones vanish after the `ClientHello` | MTU black hole | Clamp MSS; check ICMP "fragmentation needed" |

Compare a capture from both ends. If the sender shows a packet leaving and the receiver never sees it, the loss is in between. Keep packet files confidential and delete them when the case closes.

**Server-side queues.** A listener has an *accept queue*: connections whose handshake is done but that the process has not yet `accept()`ed. For listening sockets, `ss -ltn` shows the current queue length in `Recv-Q` and its limit in `Send-Q`. A queue at its limit means the process is too slow to accept; further `SYN`s or `ACK`s are dropped, which clients see as timeouts that look like network loss. `nstat -az TcpExtListenOverflows TcpExtListenDrops` confirms it. The remedy is in the application (more workers, faster accept loop), not the firewall.

## TLS beyond defaults

Protocol versions and cipher suites should follow current guidance. Mutual TLS authenticates both sides and underpins zero-trust service-to-service designs; certificate rotation at scale needs automation and short lifetimes. Revocation is weak in practice; short-lived certificates reduce reliance on it. Pinning reduces CA trust at the cost of operational fragility. SNI-based routing, ALPN and session resumption influence behaviour behind proxies.

**Handshake cost and size.** A TLS 1.3 full handshake needs one round trip; resumption can avoid the certificate exchange; 0-RTT early data removes a round trip but is replayable, so allow it only for idempotent requests. A long certificate chain (leaf, two intermediates, cross-signs) enlarges the server's first flight; if it exceeds the initial congestion window (about ten segments, ~14 KB) the handshake may need an extra round trip on high-latency links. Send only the chain clients need, and prefer ECDSA certificates to shrink size and CPU.

**SNI and routing.** SNI is visible in the `ClientHello` (encrypted ClientHello is deployed gradually). Balancers route on it; a client that omits SNI, or a health check that connects by IP without it, may receive the default certificate and fail verification: "works by hostname, fails by IP" often means exactly this. Always test with `openssl s_client -connect IP:443 -servername NAME`.

**Certificate Transparency and CAA.** Public CAs log issuances to append-only logs. Monitor logs for certificates issued for your names that you did not request, and set `CAA` records so only the CAs you use may issue.

**Trust store management.** Applications bundle trust stores (language runtimes, containers, mobile apps, old appliances) that age independently of the operating system. A CA's chain change or root expiry affects each store on its own schedule, which is why the same certificate can validate on one client and fail on another.

## Failure modes at scale

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Connection-tracking exhaustion | Many short flows through NAT | Larger tables, pooling, keep-alives |
| Ephemeral-port exhaustion | Outbound connections to one destination | Connection reuse, more source addresses |
| MTU black holes | Fragmentation blocked, path MTU discovery broken | Clamp MSS, consistent MTU |
| DNS amplification of load | Chatty clients, low TTLs, long search paths | Node-local caches, fewer lookups |
| Asymmetric routing | Return path differs and stateful filters drop it | Consistent route design |
| Certificate expiry outage | No monitoring or automation | Expiry alerts, automated renewal |
| Retry storms | Clients retry simultaneously after a blip | Backoff with jitter, retry budgets |
| Listen-queue overflow | Slow `accept()`; bursts | Workers, backlog, load shedding |
| Idle-flow expiry | NAT or balancer drops a quiet connection; the next packet gets `RST` | Keep-alive shorter than the smallest idle timeout on the path |

**Port exhaustion arithmetic.** On Linux the default ephemeral range is 32768–60999: 28,232 ports. A connection to a given *(destination address, destination port)* from one source address occupies one source port, and a closed connection lingers in `TIME_WAIT` for 60 s. The sustainable rate of *new* connections to a single destination from one source address is therefore about \(28{,}232 / 60 \approx 470\) per second. A service making 2,000 outbound short-lived calls per second to one API will fail, with `EADDRNOTAVAIL` or timeouts, unless it reuses connections or spreads across source addresses. A NAT gateway has the same constraint per translated address and destination, usually at a documented limit (for example, tens of thousands of simultaneous connections per destination), which is why a retry storm to one provider can exhaust a NAT device while all other traffic looks healthy.

```bash
ss -s                                         # socket totals, TIME-WAIT count
ss -tan state time-wait '( dport = :443 )' | wc -l
sysctl net.ipv4.ip_local_port_range net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max
dmesg | grep -i 'nf_conntrack: table full'
```

**MTU and MSS arithmetic.** An Ethernet path commonly carries 1,500-byte IP packets. TCP over IPv4 uses 20 bytes of IP header and 20 of TCP, so the maximum segment size is \(1500 - 40 = 1460\). A tunnel (VPN, overlay network) adds its own header: with a 1,400-byte tunnel MTU the usable MSS is 1,360. If a host still advertises MSS 1,460, full-sized segments exceed the tunnel MTU and are dropped when the "don't fragment" bit is set; path MTU discovery would signal this with an ICMP "fragmentation needed" message, but if that ICMP is filtered, the sender never learns and the connection stalls. Symptoms: small requests succeed, large responses or TLS certificates hang. Probe with `ping -M do -s 1372 <ip>` (payload plus 28 bytes of headers must fit the MTU) while stepping the size, and fix with MSS clamping on the tunnel endpoint and consistent MTUs, and by never filtering the needed ICMP types.

## Hypothesis ranking: "works from my laptop, times out from production"

Start from the hypotheses, then pick the cheapest experiment that splits them.

| Hypothesis | Experiment from the production host (or a debug Pod) | Eliminates / confirms |
| --- | --- | --- |
| DNS resolves differently (split-horizon or stale cache) | `dig +short name @<resolver>` versus `getent hosts name`; compare with laptop | Different answers confirm; same answers eliminate DNS |
| Route or security-group/firewall drop | `nc -vz -w 3 <ip> 443`; `ip route get <ip>` | Timeout with a correct route points at a filter; refusal means the host is reachable |
| MTU black hole (small requests work, large ones hang) | `ping -M do -s 1472 <ip>` stepping the size down; `curl` with a large POST | Failure above a size confirms; hang after the TLS ClientHello is typical |
| Ephemeral-port or conntrack exhaustion | `ss -s`; `sysctl net.netfilter.nf_conntrack_count`; kernel log | Counts near limits confirm; intermittent failures at peak |
| TLS or SNI mismatch | `openssl s_client -connect <ip>:443 -servername name -brief` | Alert or wrong certificate confirms |
| Egress proxy or policy only applied in production | `env \| grep -i proxy`; compare `curl -v` output | Different path confirms |
| IPv6 path broken, IPv4 fine (or reverse) | `curl -4`, `curl -6`; `dig AAAA` | One family fails: the other is a workaround and the fault is localised |
| Accept-queue overflow on the target | `ss -ltn` on the server; `nstat` listen counters | Queue at limit and drops confirm |

Order the experiments by cost and by how much of the hypothesis space each removes. Record what you did *and what it ruled out*, not only what you found.

## `ndots` amplification, worked

With `ndots:5` and search domains `ns.svc.cluster.local svc.cluster.local cluster.local`, resolving `api.example.com` (two dots, fewer than five) tries each search suffix first, in both A and AAAA forms, before the real name:

```text
api.example.com.ns.svc.cluster.local     NXDOMAIN
api.example.com.svc.cluster.local        NXDOMAIN
api.example.com.cluster.local            NXDOMAIN
api.example.com.                         answer      # 4 names x 2 record types = up to 8 queries
```

A client making 1,000 lookups per second can become 8,000 queries per second against the resolver, with timeouts appearing as application latency. Mitigations: use fully-qualified names with a trailing dot, lower `ndots` where appropriate, run a node-local cache, and reuse connections. The cloud-network resolver's per-interface packet limit (commonly on the order of a thousand packets per second) is a typical hidden ceiling: queries beyond it are silently dropped, so the symptom is intermittent `SERVFAIL` or multi-second delays without any resolver "outage".

## Hybrid and multi-region networks

### Hybrid: connecting on-premises and cloud

Hybrid connectivity fails in ways that single-network designs do not.

- **Address planning.** The cloud ranges, on-premises ranges, partner ranges and any future acquisition's ranges must not overlap. If they already do, your options are NAT between them (fragile; breaks address-based logging and some protocols), renumbering (expensive), or exposing services through private endpoints that sidestep routing.
- **Routing protocol and failover.** Dynamic routing (BGP) between sites and cloud lets a failed link withdraw its routes so traffic moves to the backup. Control preference deliberately: longest prefix wins first, so advertising a more specific prefix on the backup defeats failover; otherwise attributes such as local preference and AS-path length decide, and the cloud provider's own tie-break rules apply when routes are equal. Test the failover by actually dropping the primary.
- **Asymmetric paths.** If the primary link carries traffic out and the backup carries replies back, stateful firewalls at the site drop the replies. Place state where both directions pass, or make routing symmetric.
- **MTU.** Tunnels (VPN, overlay) reduce MTU; dedicated links may differ from the internet path. Standardise and clamp MSS.
- **DNS across the boundary.** Cloud workloads need to resolve on-premises names and the reverse. Use forwarding rules (conditional forwarders, resolver endpoints) in both directions, with *redundant* forwarders, and test a name that exists only on the other side. A forwarding loop (A forwards to B, B forwards back) produces timeouts that look like packet loss.
- **Security boundaries.** A private link is not a trusted link: authenticate and authorise at the application layer, segment on arrival, and log what crosses.
- **Capacity and latency.** A chatty application moved to the cloud while its database stays on-premises turns microsecond calls into milliseconds each; a page that makes 200 sequential queries over a 5 ms link takes a full second more. Measure round trips per request before moving halves of a system apart.

### Multi-region

| Design | Behaviour | Strengths | Hazards |
| --- | --- | --- | --- |
| Active–passive | One region serves; a standby is ready | Simple data story | Standby rots without tests; failover is a rare, high-stress event; data lag loses writes |
| Active–active, partitioned | Each region serves its own users or shards | Isolation; low latency; blast radius contained | Rebalancing; users who move; cross-region queries |
| Active–active, shared data | Every region serves every user | Best availability on paper | Conflict resolution, global consistency cost, hard-to-reason failure modes |

Principles that survive contact with real incidents:

- **Static stability.** During failover, depend only on things that already exist and work, not on a control plane that may be degraded by the same event. Pre-provision capacity; pre-create records; avoid designs where recovery requires launching resources in a region that is itself failing.
- **Global control planes are shared fate.** A single DNS provider, a single identity provider, a single certificate issuer or a single configuration service means "multi-region" has one failure domain after all. Inventory shared dependencies and decide which are acceptable.
- **Latency is physics.** Cross-continent round trips are tens to over a hundred milliseconds; synchronous cross-region writes cost that on every commit. Choose consistency per data type, and state the recovery-point objective in terms of acknowledged-but-lost writes.
- **Failover is a business decision.** Automated regional failover that triggers on a transient blip can cause an outage larger than the one it avoids. Many teams automate detection and require a human (or a strongly damped rule) to commit, with a rehearsed procedure and a defined failback.
- **Test it routinely.** Failover that has never been used does not work. Run game days where a region is deliberately removed from rotation.

## Zero-trust networking

**Zero trust** (as described in NIST SP 800-207 and similar guidance) means *no implicit trust from network location*: being inside the private network grants nothing. Every request is authenticated, authorised against policy, encrypted, and logged, using the identity of the caller and the state of its device or workload.

Components and how the chapter's earlier ideas map to them:

| Principle | Implementation | Failure to design for |
| --- | --- | --- |
| Workload identity | Short-lived X.509 or token identities issued per workload (for example SPIFFE-style IDs such as `spiffe://example.org/prod/orders-api`) | Issuer outage: workloads cannot renew |
| Mutual authentication | mTLS at the proxy, mesh or application | A rotation that misses a peer; clocks that disagree |
| Policy by identity | "`orders-api` may call `payments` `POST /charge`" | Policy drift; deny-by-default that blocks a new dependency in an incident |
| Policy enforcement point | Sidecar, gateway, host agent | The enforcement point becoming a single point of failure or latency |
| Continuous verification | Frequent re-issuance; logs of every decision | Alert fatigue; log volume |
| Human access | Per-session, identity-aware proxy instead of VPN to a flat network | Proxy outage locks operators out: build break-glass |

Zero trust does **not** remove network controls; it assumes they will fail and adds layers. Segmentation, security groups and egress rules still limit blast radius; identity-based policy decides what is *allowed within* that reach.

**Operating mTLS at scale.**

- Issue **short-lived** certificates (hours to days) from a highly available issuer; renew at about one-third to one-half of lifetime, so a transient issuer outage does not become a fleet outage.
- **Overlap trust bundles** during CA rotation: distribute the new CA to every verifier *before* any workload presents a certificate from it, and remove the old one only after every certificate it issued has expired.
- Make time a dependency you monitor: certificates are validated against local clocks.
- Include **break-glass** paths with their own audit.
- Measure **handshake failures by reason** (`unknown_ca`, `certificate_expired`, `bad_certificate`) as a primary reliability signal.

## Traffic engineering

Traffic engineering is controlling *where* traffic goes, to meet latency, cost, capacity and resilience goals.

| Tool | What it controls | Granularity | Caveat |
| --- | --- | --- | --- |
| Weighted DNS | Fraction of *resolutions* per target | Coarse; limited by caching | Clients and resolvers are not evenly distributed, so weights are approximate |
| Latency- or geo-based DNS | Region chosen by resolver location or measured latency | Per resolver, not per user | Users behind distant resolvers are misplaced |
| Anycast | Same address from many sites; routing picks the nearest | Network-level | Convergence delay; stateful connections can shift when routes change |
| Load-balancer weights, canaries | Share of *requests* | Fine; per request | Needs health signals and rollback |
| BGP attributes (local preference, prepending, communities) | Outbound and, indirectly, inbound path selection | Per prefix | Inbound control is influence, not command; mistakes propagate widely |
| Connection draining, outlier ejection | Move traffic off sick targets | Per target | Thresholds that eject too much create cascades |

**Canary and shift procedure for a network change.** Move 1% of traffic (by weight or header); compare error rate, latency percentiles and TLS failures between cohorts for one full traffic cycle; step to 5%, 25%, 50%, 100%; keep the old path warm until a rollback decision window closes. DNS-based shifts are slow to *reverse* because of caching: use balancer-level shifts for anything that you may need to undo quickly.

**BGP, briefly, because it fails loudly.** The internet is a set of autonomous systems exchanging reachability for prefixes. A route announced by a wrong party (leak or hijack) can pull traffic into a black hole; **RPKI route-origin validation** lets networks reject announcements that do not match the registered origin. For your own prefixes: publish route-origin authorisations, monitor announcements from outside, use maximum-prefix limits on sessions, and rehearse withdrawing and re-announcing. A widely discussed 2021 outage of a large platform shows how DNS and routing interlock: its authoritative DNS servers were designed to withdraw their own route announcements when they judged the backbone unhealthy, so a backbone fault removed the DNS servers from the internet, which also removed the tools needed to repair the backbone. Design **out-of-band** access and ensure your recovery path does not depend on the thing that has failed.

## Designing for partial failure

**Gray failure** is a component that is "up" by its own and its monitor's checks and degraded for real users: a node that answers health checks but drops one in fifty requests; a path that is fine for small packets and not large ones; one zone with 800 ms disk latency. Binary health checks cannot see it; request-level success and latency per target and per path can.

Defences work together:

- **Timeouts on every network call**, derived from a deadline passed along the call chain (each hop gets what remains, not a fresh budget).
- **Bounded retries** with exponential backoff and jitter, a retry budget (for example, at most 10% extra requests), and **idempotency keys** so retries are safe.
- **Circuit breakers** that open after repeated failures and probe cautiously to close.
- **Load shedding** and admission control: refuse early rather than queue to death.
- **Bulkheads:** separate pools and limits per dependency so one slow downstream cannot absorb all threads.
- **Outlier ejection** at the balancer: remove targets whose error rate or latency is far from the fleet's, with a ceiling on how many may be ejected.
- **Hedged requests** for latency-sensitive idempotent reads: send a second request after the p95 delay and use whichever returns first, accepting a small load increase.
- Health checks that distinguish *dead instance* from *degraded dependency*.

**Partial failure design with numbers.** Suppose a dependency usually answers in 50 ms and degrades to 5 s. A caller with a 30 s timeout and three retries holds a thread for up to two minutes per request; with 200 threads the caller is exhausted within seconds, and callers of *that* service then fail. Defences work together: a per-call timeout close to p99 (for example 300 ms), at most one retry with jittered exponential backoff (`sleep = random(0, base × 2^attempt)`), a retry budget of about 10% of requests, a circuit breaker that opens after repeated failures, and a fallback or fast 503. Retries are safe only for idempotent operations; use idempotency keys for payments or order creation.

**Little's law explains the collapse.** Concurrency in use equals arrival rate times time in system. At 1,000 requests per second and 50 ms, about 50 workers are busy; at 5 s, 5,000 would be needed, so 200 workers saturate almost immediately. Retries multiply the arrival rate at the same moment capacity falls, which is why retry storms convert a degraded dependency into a total outage.

**Retry amplification across tiers.** With three layers each retrying three times, one user request can create \(3^3 = 27\) calls to the bottom layer. Retry at *one* layer (usually the edge or the layer closest to the failure) and propagate a "do not retry" signal downward.

## DNS and TLS incident patterns

### Pattern catalogue

| Incident | Mechanism | Signature | Prevention / response |
| --- | --- | --- | --- |
| Expired leaf certificate | No monitoring or renewal hook failed | `certificate_expired` alerts; spikes in handshake failures | Per-name expiry alerts; test renewal; automation |
| Expired intermediate or root in a chain | A CA certificate in the chain ends; some clients lack alternative paths | Works for new clients, fails for old trust stores or specific libraries | Inventory chains; monitor every certificate in the chain; stay on current chains |
| Wrong or missing intermediate after rotation | Deployment sent only the leaf | Browsers work, API clients fail | Serve full chain; test with a strict client |
| Name mismatch after migration | New endpoint lacks the old name in its SAN | Failures only for clients using the old name | Union SANs during migration; test each hostname |
| Clock skew | A host's clock drifts | `not yet valid` or `expired` on valid certificates; failing mTLS for a subset | Time synchronisation monitoring |
| Lame or broken delegation | `NS` points at servers that do not serve the zone | `SERVFAIL` for some resolvers; intermittent | Check delegation from the parent; monitor `NS` and SOA serials on all servers |
| Stale secondary | One name server has an older zone | Different answers depending on which server answers | Compare SOA serial across all authoritative servers |
| DNSSEC key mismatch | `DS` no longer matches the zone key | `SERVFAIL` only on validating resolvers | Coordinate key and `DS` changes; staged rollover |
| TTL not lowered before change | Cached old answers persist | Split traffic for as long as the old TTL | Lower TTL ahead of the change by at least the old TTL |
| Cached negative answer | `NXDOMAIN` cached before the record existed | Record exists but is "missing" for some | Create records before use; mind SOA negative TTL |
| Dangling record | Name points at a decommissioned resource | Takeover risk; failures | Inventory and expiry on DNS records |
| DNS dependency loop | Recovery tooling needs the failing name | Cannot deploy the fix | Out-of-band access; IP-literal break-glass |
| Resolver saturation | Chatty clients; amplified lookups | Latency and `SERVFAIL` at peak | Node-local caches; reduce lookups; capacity |
| Inconsistent CDN or proxy certificate | One edge node has an older certificate | Failures for a fraction of requests | Compare all edges; staged deploys |

### Composite case A — an internal CA expires

*Timeline (illustrative).* 09:02 deployment finishes; 09:05 error rate on service-to-service calls rises from 0.1% to 2%; 09:12 pages fire for several services; 09:20 `bad_certificate` and `certificate_expired` appear in sidecar logs; 09:35 someone notices the *intermediate* CA certificate expired at 09:00. Workload certificates were being renewed automatically and were individually valid; the issuing intermediate that signed them had expired.

*Mechanism.* Inventory covered workload certificates but not the CA chain. Verifiers began rejecting any certificate that chained through the expired intermediate; as workloads restarted or renewed, more of them presented the old chain, so failures grew steadily rather than all at once.

*Detection gap.* Alerts watched leaf expiry. No test verified the chain's own validity dates.

*Resolution and prevention.* Issue a new intermediate; distribute it; force renewal. Add days-to-expiry for *every* certificate in every chain; give CAs long runway and an owner; rehearse a CA rotation with overlapping trust bundles in staging; add a synthetic strict-client probe.

### Composite case B — failover that did not fail over

*Symptoms.* A health-checked DNS failover to the standby region triggered in 90 s as designed; users in one segment still failed for 25 minutes.

*Mechanism.* Three causes stacked: (1) a long-running client library cached the address for the process lifetime; (2) a large enterprise customer's resolver enforced a minimum TTL of 15 minutes; (3) connection pools held connections to the dead region and retried on them with long timeouts. The measured failover for that segment was dominated by client behaviour, not DNS.

*Prevention.* Put failover below DNS where possible (a balancer that routes to healthy regions or zones); make pools recycle connections; test failover from the client's perspective, with real client libraries; publish a customer-facing note about resolver caching; document that DNS-only failover cannot meet objectives below the longest well-known cache.

### Composite case C — NAT exhaustion after a "harmless" release

*Symptoms.* Outbound calls to a payment provider time out at peak. CPU is low; the provider reports no problem; retries make it worse.

*Mechanism.* A release switched an HTTP client to a library default that did not reuse connections. Connections to one provider IP from one NAT address consumed source ports faster than they were released (`TIME_WAIT`), and the NAT device began dropping new flows. The provider's address set was small, so the per-destination limit was reached quickly; retries multiplied new connections.

*Detection gap.* NAT port-allocation errors were collected but not alerted; the release test ran at one-tenth of peak.

*Prevention.* Enforce connection reuse in a shared client; alert on port-allocation errors; spread across multiple NAT addresses for heavy single destinations; include outbound-connection counts in load tests and in release review.

### Incident analysis structure for a network failure

Timeline with timestamps and data sources; the hypotheses considered and how each was ruled out; the actual mechanism; the detection gap (why no alert fired first); mitigations with owners and dates. Add: what *made it worse* (retries, restarts, automated actions), what *limited the blast radius*, and which assumption the design had silently made.

## Security versus availability

Every network security control can cause an outage; every availability measure can open an attack path. The expert's task is to choose **how each control fails**.

| Control | Fail-closed (secure) | Fail-open (available) | Choose by |
| --- | --- | --- | --- |
| WAF or inspection layer | Block all if inspection is down | Pass traffic uninspected | Value at risk versus cost of an outage; rate-limit and alert in both cases |
| mTLS enforcement | Reject unauthenticated calls | Accept plain connections | Sensitivity of the data; staged rollout with permissive mode and metrics |
| Certificate revocation check | Reject if status unknown (hard fail) | Accept if status unknown (soft fail) | Practical default is soft fail with short certificate lifetimes |
| Deny-by-default network policy | New dependency blocked until approved | Allow-list wide ranges | Fast exception process, logged and expiring |
| DNS filtering or sinkholes | Block unknown names | Allow with logging | Threat profile; false-positive handling |
| Identity provider for operators | No access if IdP down | Local break-glass | Break-glass with strong audit |
| Rate limiting and DDoS protection | Drop above threshold | Allow bursts | Protect dependencies first; allow-list critical clients |

Guidelines:

- **Decide fail-open or fail-closed per control, write it down, and test the failure.** Unexamined defaults are decisions made by accident.
- **Stage enforcement:** audit mode, then warn, then enforce, measuring would-have-blocked traffic at each step.
- **Keep break-glass real:** access that works when SSO, DNS, the certificate issuer and the network controller are all unavailable, with alarms and review; test it quarterly.
- **Avoid security controls that need the failing system to be repaired.** If your firewall policy server must be reachable to change policy, an outage in that path becomes unrepairable.
- **Pinning:** it reduces exposure to mis-issuance at the price of brittleness. Pin to a CA or key set you control and can rotate; avoid pinning to a leaf you cannot replace without an app release.
- **Emergency changes:** a loosened rule or disabled check during an incident must carry an expiry and a ticket; "temporary" exceptions are a classic long-term exposure.
- **Measure the cost of blocking:** false-positive rate, blocked legitimate calls and time-to-exception are service-level indicators for the security control itself.

## Trade-offs: mTLS, short-lived certificates, pinning

| Option | Gain | Operational cost | Typical failure |
| --- | --- | --- | --- |
| Mutual TLS | Both sides authenticated; identity-based policy | Issuance and rotation for every workload; debugging two-sided handshakes | A rotation misses a client and calls fail with `bad_certificate` |
| Short-lived certificates (hours to days) | Less reliance on weak revocation; small exposure window | Needs reliable automation and a highly available issuer | Issuer outage becomes a fleet-wide outage when certificates expire |
| Pinning | Resists mis-issuance by other authorities | Brittle; any legitimate key change breaks clients | Forced emergency key change locks out clients without an update |

Design for the *failure mode of the control*: monitor days-to-expiry for every certificate and for the issuer's own chain, overlap validity periods during rotation, and test rotation in staging with a deliberately short lifetime. A CA certificate that expires without a plan takes down everything that trusts it, so give CAs long runway, an inventory of dependents and a rehearsed replacement.

**Why `curl -k` misleads.** It disables validation, so the one thing you are testing (the certificate chain) is skipped. Use `openssl s_client -showcerts`, `curl --cacert`, and `curl -v` to read the verification error, and compare dates, names (`subjectAltName`) and chains.

## Migrations without outages

Network, DNS and TLS migrations are where the earlier mechanisms converge. A reliable pattern: **expand, verify, shift, contract**.

1. **Expand:** make the new thing exist beside the old (new network, new endpoint, new certificate with a SAN union, new name server).
2. **Verify:** test the new path from real client vantage points, including the oldest supported clients and resolvers.
3. **Shift:** move traffic in measured steps, with a fast rollback.
4. **Contract:** after a defined observation window (longer than the longest relevant cache), remove the old thing, and record that you did.

### DNS cutover

- Lower TTL **at least one old TTL** ahead; confirm the lowered TTL is being served by *every* authoritative server.
- Pre-create the new records; ensure both old and new targets answer correctly for all hostnames, including `Host`/SNI behaviour.
- Switch (or shift by weight); watch traffic on **both** targets; expect a tail of clients on the old target for up to the old TTL plus uncooperative caches.
- Keep the old target serving, with a redirect or proxy if feasible, until traffic has drained; only then decommission.
- Raise TTL after stability; record the date.

### Moving DNS providers (or enabling DNSSEC)

1. Export the zone, import to the new provider, and **diff every record type**, including apex records, `TXT`, `MX`, `CAA` and provider-specific alias records, which often do not transfer.
2. Query the new provider's name servers directly for every name and compare with the old answers.
3. Lower TTLs on the `NS` set at the parent where possible (parent TTLs are often long and outside your control); keep the old provider serving the same zone during the transition.
4. Change delegation. If DNSSEC is in use, plan the `DS` change carefully (either disable cleanly first or use a documented multi-signer procedure); a mismatch causes `SERVFAIL` for validating resolvers only.
5. Monitor query rates at both providers; decommission the old after the old `NS` TTL and a safety margin.

### Certificate and CA migration

- Issue the new certificate **with the union of names** during the transition; deploy to a single canary endpoint; verify with strict clients; roll out.
- When changing issuers, verify the chain against every trust store you support, including old runtimes and appliances; check certificate-pinning clients.
- For an internal CA change, distribute the new trust anchor first (weeks before), then switch issuance, then retire the old after the maximum workload certificate lifetime plus margin.
- Keep monitoring *both* chains throughout.

### Network re-addressing and consolidation

- Establish connectivity between old and new ranges first (peering or transit with non-overlapping ranges), then move workloads in groups, updating security-group references, DNS records and allow-lists *at third parties* (who often take days to change).
- Treat IP allow-lists held by partners and customers as a dependency list: inventory them; provide stable egress addresses (dedicated NAT or elastic addresses) so future moves do not require their changes.
- Migrate data-plane traffic before control-plane and management paths, keeping break-glass on both sides.
- Rehearse rollback: for every step, write how to undo it and how long that takes.

### Enabling IPv6 or changing a load balancer

Add `AAAA` records only after every component (balancer, firewall, application logs, rate-limiters, allow-lists) handles IPv6; monitor IPv6 separately; remember that `AAAA` changes who your clients are connecting as, so rate-limit keys and allow-lists keyed on IPv4 will mis-handle them. For a balancer change, run old and new in parallel behind weighted records or a staged DNS switch, compare per-request metrics, then drain.

## Expert checklists

**Before a change to networking, DNS or TLS**

- Blast radius stated in terms of users and dependencies.
- Rollback written, timed and tested.
- Caches considered: DNS TTLs, negative TTLs, connection pools, trust stores.
- Monitoring in place on *both* old and new paths.
- Break-glass access verified independent of the thing changing.
- Time window chosen so that the people who understand the system are available.

**During an incident**

- Confirm scope with a third vantage point before theorising.
- Prefer reversible actions; record every change with a timestamp.
- Do not restart or flush until evidence (captures, state, counters) is saved.
- Watch for amplification: retries, restarts, automated failovers.

## Knowledge consolidation

- Expert failures are **partial**; the boundary between working and failing clients, paths or sizes is the clue.
- DNS, TLS and TCP each have **hidden limits**: UDP size, DNSSEC validation, accept queues, ephemeral ports, conntrack, MTU/MSS, chain size. Compute them rather than guess.
- **Hybrid and multi-region designs** fail at seams: overlapping addresses, asymmetric paths, shared control planes, DNS forwarding, cache behaviour. Static stability and rehearsed failover matter more than diagrams.
- **Zero trust** replaces location-based trust with workload identity, short-lived credentials and per-request policy, and adds new dependencies (issuer, policy plane) that need their own availability design.
- **Traffic engineering** tools differ in granularity and reversibility; DNS is coarse and slow to undo, balancers are fine and fast.
- **Partial-failure design** is timeouts with deadlines, bounded retries, breakers, load shedding, bulkheads and outlier ejection, justified by arithmetic such as Little's law.
- **Security controls are availability risks**; decide fail-open versus fail-closed deliberately and test the failure.
- **Migrate by expanding, verifying, shifting and contracting**, with observation windows longer than the longest cache.
- **Write incidents as mechanisms and detection gaps**, not as blame.

## Exercises

**Exercise 1 — Port arithmetic.** A service makes 3,000 new outbound HTTPS connections per second to one API address from one host with the default port range. Compute the sustainable rate, explain what fails, and propose three fixes with their costs. Reproduce a scaled-down version in a lab by narrowing `ip_local_port_range`.

**Exercise 2 — MTU hunt.** On a lab VPN or overlay with MTU 1,400, show that small requests succeed and large ones stall when ICMP is blocked. Use stepped `ping -M do` and a packet capture to find the black hole; fix by MSS clamping; prove with a capture.

**Exercise 3 — DNSSEC failure.** In a lab zone, deliberately mismatch the `DS` record. Show `SERVFAIL` from a validating resolver and success from one with validation disabled, using `+cd`. Document the recovery.

**Exercise 4 — ndots.** In a container or cluster lab, capture DNS queries for an external name with default `ndots`. Count the queries; reduce them with a trailing dot, with a lower `ndots` and with a node-local cache; report each result.

**Exercise 5 — Failover reality.** Build a two-target DNS failover with health checks. Measure client-observed recovery time from three client types (curl, a long-running script, a pooled HTTP client). Explain differences and redesign to meet a 60-second objective.

**Exercise 6 — CA rotation rehearsal.** Create a private CA hierarchy with a 24-hour intermediate. Run services with mTLS and short-lived leaf certificates. Rotate the intermediate with overlapping trust and no failed calls; then repeat while "forgetting" one verifier, and show how the failure presents.

**Exercise 7 — Retry storm.** Build a caller and a dependency whose latency can be raised from 50 ms to 5 s. Show collapse with naive retries and 30 s timeouts; then add timeouts, a retry budget, a breaker and load shedding. Report success rate, latency and load on the dependency in each case.

**Exercise 8 — Fail-open versus fail-closed.** For five controls in your environment (WAF, mTLS, revocation checks, policy engine, IdP), record the current failure behaviour, the business impact of each failing in each direction, and the decision you would make. Test one.

**Exercise 9 — Migration plan.** Write a plan to move `orders.example.com` and its certificate to a new provider, covering TTLs, SANs, DNSSEC, canary, rollback, observation window and decommissioning. Identify the three assumptions most likely to be wrong.

**Exercise 10 — Postmortem.** Write the post-incident analysis for Composite case B in the structure given, adding what made it worse, what limited the blast radius and the assumption the design had made.

**Solution notes.**

*Exercise 1.* Sustainable new-connection rate to one destination is about 28,232 / 60 ≈ 470 per second; 3,000 per second exceeds it by roughly six times, so new `connect()` calls fail with address-not-available or time out. Fixes: connection reuse (most effective, needs client changes and keep-alive tuning), more source addresses or NAT addresses (cost, allow-list changes), destination spreading (needs multiple endpoints), shorter `TIME_WAIT` handling (limited and risky; generally not recommended). Narrowing the range shows the same failure at a lower rate.

*Exercise 2.* Small `ping` succeeds; payloads above the tunnel capacity fail with "message too long" or silence if ICMP is dropped. The capture shows large segments leaving and never acknowledged, retransmitted with the same size. MSS clamping makes the SYN advertise a smaller MSS and the large transfers succeed.

*Exercise 3.* `SERVFAIL` with validation, a normal answer with `+cd`, and `dig DS`/`DNSKEY` showing disagreement. Recovery restores the matching `DS` or removes it and waits for the parent's TTL.

*Exercise 4.* Expect up to eight queries per lookup with `ndots:5` and three search domains (A and AAAA for four names); a trailing dot yields two (A, AAAA), a lower `ndots` similarly, and a node-local cache removes repeated upstream queries.

*Exercise 5.* Typical results: `curl` recovers after the TTL expires; the long-running script never recovers until restarted if it resolved once; the pooled client recovers only after its connections break or are recycled. To reach 60 s, move failover below DNS (balancer), set pool lifetimes, and reduce TTL and detection time.

*Exercise 6.* Success shows both CAs in every bundle before issuance switches; the forgotten verifier shows `unknown_ca` for new certificates only, which begins as workloads renew, producing a slowly widening failure.

*Exercise 7.* Naive version: thread or connection exhaustion within seconds and zero throughput; protected version: bounded latency, some fast failures, dependency load capped near the budget. Report the dependency's requests per second, which should not exceed about 1.1 times the baseline with a 10% budget.

*Exercise 8.* Look for explicit decisions with justification, and a test that demonstrates the actual failure behaviour rather than the documented one.

*Exercise 9.* Strong answers include a union-SAN certificate on the canary, per-server TTL verification, a full zone diff, an observation window longer than the old TTL and parent `NS` TTL, and named assumptions such as "all resolvers respect TTLs" and "no partner has the old IP allow-listed".

*Exercise 10.* The analysis should name the mechanisms (client caching, minimum-TTL resolver, pools), the detection gap (monitoring from inside the provider's path), the aggravator (retries on dead connections) and the silent assumption ("DNS failover is complete when the record changes").

## Mentoring prompts

A service works from your laptop and times out from production; list the first five experiments you would run and what each would rule out. Why is `curl -k` usually the wrong tool for investigating a certificate problem? How would you design certificate rotation so that an expiring CA does not take the company offline? Explain why DNS-only failover cannot meet a 30-second recovery objective, and what you would build instead. Which of your security controls fail closed, which fail open, and have you ever tested either? What makes a multi-region design "one failure domain with extra steps", and how would you find the shared dependency?

---

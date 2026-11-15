# T-CLD-02-P — Professional Engineering

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-p"></a>
#### T-CLD-02-P — Professional Engineering

## Why this matters

At the Professional level the network is not something you debug; it is something you **design, document and operate**. The questions change from "which hop failed?" to "which hops *may* exist, who decided so, how will we know when one breaks, and what happens to users while it is broken?" Most serious network incidents are not exotic: an unrenewed certificate, a TTL nobody lowered, a route table edited in one zone only, a single NAT device for three zones, a firewall rule nobody could explain. Each is preventable with a written design, automation, monitoring and a rehearsed procedure.

This section keeps the neutral `orders-api` example. Where a managed cloud makes the idea concrete, AWS-style terms (security group, route table, NAT gateway) are used, with the general principle stated first; other providers have close equivalents.

## An ordered diagnostic method, as a runbook

Write the method down so another engineer can follow it at 03:00:

1. **Name:** resolves? (`dig`, `getent hosts`) from where the client runs.
2. **Route:** does the client have a path? (`ip route get`, route tables, traceroute where permitted)
3. **Port:** open? (`nc -vz -w 3`, `curl -m`) — refused versus timeout.
4. **TLS:** handshake OK, name and chain valid, not expired?
5. **Process:** answering correctly? (status code, body)
6. **Dependency:** database, queue, downstream API healthy?

State results as evidence ("timed out after 3 s at hop 3 from client subnet A; succeeded from subnet B") rather than conclusions. Always test **from the affected vantage point** — a laptop result says nothing about a production subnet — and record the source, destination, time and exact command.

## Trust zones: designing who may talk to whom

A **trust zone** is a set of systems that share a security posture and may therefore trust each other more than they trust the outside. Network controls turn that intent into enforceable rules.

```text
                    Internet
                       │  443
               ┌───────▼────────┐
  EDGE zone    │ Load balancer  │   public subnets: route to internet gateway
               └───────┬────────┘
                       │ 8080 (re-encrypted)
               ┌───────▼────────┐
  APP zone     │  orders-api    │   private subnets: egress via NAT, no inbound from internet
               └───────┬────────┘
                       │ 5432
               ┌───────▼────────┐
  DATA zone    │  database      │   private subnets: no default route at all
               └────────────────┘
  MGMT zone:   bastion / session manager, CI runners, monitoring — separate, tightly scoped
```

Design principles:

- **Default deny between zones; allow explicit flows.** Each allowed flow is a row in a table with an owner and a reason.
- **Reference identities, not addresses.** Where the platform allows, a security-group rule says "allow 5432 from members of `orders-api-sg`" rather than "from `10.50.0.0/20`". Membership follows the workload as addresses change, and the rule documents *who* is allowed.
- **Least privilege on egress too.** Outbound rules limit data exfiltration and the blast radius of a compromised instance; data-zone subnets with no route to the internet cannot beacon out even if a rule is wrong.
- **Management paths are separate.** SSH from the internet to application hosts is a design failure; use a session-manager style service, a bastion in the management zone, or short-lived credentials.
- **One layer is never enough.** Security group, subnet route, network ACL, host firewall and application authentication fail independently; a design that relies on one is one mistake from exposure.

A **flow matrix** is the central artefact:

| Source | Destination | Port | Why | Control |
| --- | --- | --- | --- | --- |
| Internet | Edge LB | 443 | Customer traffic | LB security group; WAF |
| Edge LB | `orders-api` | 8080 | Forward requests | `orders-api-sg` allows from `lb-sg` |
| `orders-api` | Database | 5432 | Persistence | `db-sg` allows from `orders-api-sg` |
| `orders-api` | Payment provider | 443 | Charge cards | Egress rule + NAT, logged |
| CI runners | `orders-api` | 22 denied | No SSH | Absence of rule; verified by test |
| Monitoring | `orders-api` | 9100 | Metrics | `orders-api-sg` allows from `mon-sg` |

Every real incident adds a row, removes a row, or shows that a row was never actually enforced. **Test the negatives:** a scheduled job that attempts forbidden flows (from the app zone to the internet on an unexpected port, from the edge to the database) and alerts if they *succeed* is worth more than ten reviews.

### Writing rules you can still understand in a year

- Name rules by intent (`allow-lb-to-orders-api-8080`), not by ticket number.
- Tag every rule with owner and purpose; delete rules with no owner after review.
- Prefer managed prefix lists or groups to long lists of CIDRs; update them in one place.
- Keep rule sets in infrastructure-as-code with peer review; emergency console changes get an after-the-fact ticket and are reconciled.
- Review quarterly: unused rules (flow logs show no matching traffic) are candidates for removal.

## TLS termination and identity

"Where does TLS terminate?" is an architecture decision, not a checkbox.

| Pattern | Path | Gains | Costs / risks |
| --- | --- | --- | --- |
| Edge termination, plaintext inside | Client ⇒ LB (TLS); LB → app (HTTP) | Simplest certificate management; LB can inspect and route | Traffic unencrypted in the private network; compliance may forbid |
| Re-encryption | Client ⇒ LB (TLS); LB ⇒ app (TLS) | Encrypted on every link; LB still inspects | Two sets of certificates; internal certificates to rotate |
| TLS pass-through | Client ⇒ app via L4 balancer | App holds keys and sees client; no inspection at LB | No L7 routing at the LB; each app needs certificates; client IP handling differs |
| Mutual TLS (mTLS) between services | Both sides present certificates | Service identity; policy by identity; strong east-west protection | Issuance and rotation per workload; two-sided debugging |

Match the choice to the threat model and compliance regime. A common, defensible production baseline: public TLS terminated at the load balancer with a managed certificate, **re-encrypted** to the application with an internal certificate, and mTLS between services that handle sensitive data.

**Two different certificate worlds.** *Public* certificates (from a public CA) identify names on the internet and are validated by clients' standard trust stores. *Internal* certificates (from a private CA or a service-identity system) identify workloads and are validated only against a CA you distribute. Do not use public CAs for internal-only names you do not own, and do not hand-roll an internal CA without owning its renewal, protection of its key and distribution of its root.

**Identity versus encryption.** TLS answers "am I talking to the holder of a key certified for this name?", not "is this the *service I intend*, authorised to do this?". For service-to-service calls, bind identity to the workload (a certificate whose name or URI identifies it, such as a SPIFFE-style ID) and authorise by that identity, not by source IP.

### Certificate lifecycle

1. **Issue automatically** (ACME for public certificates, or a cloud certificate manager; an internal issuer for workloads). Humans do not paste certificates.
2. **Renew early.** Renew at roughly two-thirds of the lifetime; public lifetimes are shrinking (the CA/Browser Forum schedule reduces maximum validity in stages through the late 2020s), which makes manual renewal untenable.
3. **Keep keys out of source control and images.** Generate keys where they will be used; protect CA keys offline or in an HSM/KMS.
4. **Monitor expiry from outside, per name:** alert at 21 days (ticket), 7 days (page), 48 hours (incident). An internal inventory plus an external probe catches both unknown certificates and certificates installed on the wrong endpoint.
5. **Test the renewal path**, not just the certificate: a certificate that renews on paper but whose deploy hook fails is a delayed outage.
6. **Plan revocation realistically.** Client revocation checking is unreliable; short lifetimes and fast re-issue are the working mitigation.

```bash
# External expiry probe: days until expiry for one endpoint
end=$(echo | openssl s_client -connect orders.example.com:443 -servername orders.example.com 2>/dev/null \
      | openssl x509 -noout -enddate | cut -d= -f2)
echo $(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 )) days remaining
```

**Protocol and cipher policy.** Allow TLS 1.2 and 1.3 only (retire 1.0/1.1), prefer forward-secret key exchange, and use your load balancer's maintained security policies rather than hand-picked cipher lists. Enable **HSTS** (`Strict-Transport-Security`) for user-facing sites after verifying all subdomains support HTTPS, because a bad HSTS decision is hard to undo; start with a short `max-age`.

**What can break with termination.** At a layer-7 balancer: the backend sees the balancer's address, so use `X-Forwarded-For`/`X-Forwarded-Proto` and make the application honour them only from the proxy; redirect loops occur when the app sees plain HTTP and redirects to HTTPS forever; large headers or timeouts differ at each hop.

## DNS resilience

DNS is a dependency of nearly everything and is often the only one with no fallback. Treat it like a database.

**Authoritative side**

- Run at least **two name servers in different networks**; for high-criticality zones, consider **two independent providers**, with the zone kept in sync from code. Delegation (`NS`) lists both.
- Keep zone data in version control and deploy through review; hand edits in a console are how apex records disappear.
- Protect the registrar account (multi-factor, registry lock for critical domains) and monitor for `NS` changes: a hijacked delegation is a total outage and a security breach.
- Choose TTLs deliberately: **long** for stable records (reduces load and shields against provider blips), **short** (30–60 s) for records you fail over, and **always** lower TTLs ahead of planned changes.

**Resolver side**

- Use more than one resolver address; understand your platform's resolver and its **rate limits** (cloud resolvers often cap queries per second per network interface). Chatty clients with low TTLs and long search paths can hit them.
- Run a node-local cache where query volume is high, so repeated lookups never leave the machine.
- Know how each runtime caches: some resolve once per process, some honour TTLs only partly, and long-lived connection pools never re-resolve, so a failover that depends on clients noticing a new address will be slow whatever the TTL says.

**Failover patterns**

| Pattern | How it works | Limits |
| --- | --- | --- |
| Health-checked failover records | Provider probes the primary; if it fails, answers with the secondary | Detection time + TTL = minimum failover time; cached answers persist |
| Weighted or latency-based records | Several answers, chosen by weight or measured latency | Not a substitute for health checks unless combined with them |
| Anycast front door | Same address announced from many places | Routing converges on its own timescale; stateful flows can move mid-connection |
| Load balancer in front of everything | One stable DNS name for a balancer that handles instances | Pushes failover below DNS, with seconds rather than minutes of delay |

The simplest resilient design: **one DNS name, pointing at a load balancer that is itself multi-zone**; DNS changes are then rare, and instance health is handled where it is fast.

**Failover arithmetic.** If a health check runs every 30 s and needs 3 consecutive failures (90 s), and the record's TTL is 60 s, the worst case before *all* well-behaved clients move is about 150 s, plus clients that cache longer. Write this number in the runbook. If the recovery-time objective is 60 s, DNS-only failover cannot meet it, and the design must change.

**Private and split-horizon DNS.** Internal names (`db.orders.internal`) live in a private zone visible only inside the network; the public zone shows only what the internet needs. Document which zone answers where and test from both sides: "works internally, NXDOMAIN externally" is intentional; the reverse leaks internal topology.

**Dependency inventory.** List every external name your service resolves (payment provider, identity provider, package mirrors, telemetry). Each is a DNS-and-TLS dependency; a resolver outage or a certificate expiry at the provider is *your* outage unless you have timeouts, caching and fallbacks.

## Routing failure: finding the missing hop

Routing failures in the cloud are silent: nothing reports "route missing"; the symptom is a timeout. Work the path systematically:

```text
source instance → source subnet's route table → (NAT / gateway / peering / transit) →
   destination subnet's route table (return path) → security groups both ends → NACLs both subnets → host firewall
```

**Checklist**

1. Source and destination addresses and subnets — written down, not remembered.
2. Source route table: is there an entry matching the destination (longest prefix) and is its target healthy (a gateway in `active` state, not `blackhole`)?
3. Return route: does the destination's table route replies back to the *source* range, or to the NAT address if source NAT occurred?
4. Security groups at both ends: inbound at the destination, outbound at the source, with the right protocol and port.
5. Network ACLs: both directions, ephemeral ports for return.
6. Host firewall and listener (`ss -ltnp`).
7. Overlapping CIDRs across a peering or VPN: the packet may be sent to the wrong place or nowhere.
8. Use the platform's path-analysis tool (for example a reachability analyser) to confirm the first blocking component *before* guessing.

Typical causes, ordered by how often they occur:

| Symptom | Likely cause | Evidence |
| --- | --- | --- |
| Timeout only from one subnet | Route table missing an entry, or wrong table associated | Compare tables of working and failing subnets |
| One-way connectivity (A→B fine, B→A hangs) | Missing return route or stateless ACL | Flow logs show `ACCEPT` outbound, no reply |
| New peering does not work | Routes not added on *both* sides, or overlapping ranges | Route tables; CIDR register |
| Internet egress fails from private subnet | NAT gateway absent, in wrong zone or its route is `blackhole` | `0.0.0.0/0` target status |
| Intermittent failures at peak | NAT port exhaustion or conntrack limits | NAT error metrics, kernel log |
| Works by IP, not by name | DNS, not routing | `dig`, resolver in use |

**Never fix a route by adding a broader one first.** A `0.0.0.0/0` or `10.0.0.0/8` route "to make it work" can silently redirect other traffic. Add the most specific route that solves the problem, record why, and review with flow logs.

## Connectivity logging and observability

Without logs you can only reason; with them you can prove.

**Flow logs** record, per network interface or subnet, metadata about accepted and rejected flows. A typical record:

```text
version account-id    interface-id  srcaddr     dstaddr      srcport dstport protocol packets bytes start      end        action log-status
2       123456789010  eni-0a1b2c3d  10.50.0.15  10.50.16.20  51234   5432    6        10      840   1700000000 1700000060 REJECT OK
```

Read it: from `10.50.0.15:51234` to `10.50.16.20:5432` over TCP (protocol 6), ten packets rejected. A `REJECT` on the *destination* port with the source being your app says a security group or ACL denied it. A pattern of `ACCEPT` outbound but nothing inbound at the other end says the packet was dropped *between* — a route or a filter outside what that log sees. Flow logs do not show payloads and are aggregated over a window, so they prove *whether* traffic was allowed, not *what* it contained or the exact order of packets.

| Signal | Answers | Typical source |
| --- | --- | --- |
| Flow logs | Was this flow accepted or rejected? Who talks to whom? | Network interfaces, subnets |
| Load balancer access logs | Status, backend, latency, TLS version per request | Balancer |
| Load balancer metrics | Healthy host counts, 5xx by origin (balancer vs target), connection errors | Balancer |
| DNS query logs | Which names are resolved, `NXDOMAIN`/`SERVFAIL` rates, volume | Resolver |
| Certificate inventory | Days to expiry for every endpoint | External probe + certificate manager |
| Synthetic probes | Name → connect → TLS → response from several locations | A prober you run |
| Host metrics | Retransmits, conntrack count, socket states | Agents on hosts |
| NAT metrics | Port-allocation errors, bytes, connection counts | NAT device |

**Synthetic probes** are the most valuable single addition: from each zone (and from outside), repeatedly perform the full chain and record the *stage timings* (as in the `curl -w` command from the Beginner level). A probe that reports "DNS 2 s" tells you which hop is degrading before users complain.

**Alerting** should follow user-visible symptoms (error rate, latency, probe failures) first, with cause-oriented alerts (certificate expiry, healthy-host count, NAT errors, DNS `SERVFAIL` rate) as early warning. Every alert links to the runbook step it triggers.

**Cost and privacy.** Flow logs, DNS logs and balancer logs are voluminous and contain addresses that may be personal data. Decide retention, access and sampling up front; send them to cheap storage with a query layer, and keep a short hot window for incident work.

## Multi-AZ design

A **multi-AZ** (multi-zone) design keeps the service available when one zone fails.

```text
                  DNS name → load balancer (nodes in zones a, b, c)
        zone a                     zone b                     zone c
   public  subnet + NAT-a     public  subnet + NAT-b     public  subnet + NAT-c
   private subnet: app x N    private subnet: app x N    private subnet: app x N
   private subnet: db primary private subnet: db standby private subnet: (replica)
```

Principles:

- **One of everything per zone** on the path that must survive: subnet, NAT device, route table pointing at *that zone's* NAT. A single NAT in zone a means zones b and c lose egress when a fails, and cross-zone traffic incurs cost and latency.
- **Capacity N+1 (or better) by zone.** If three zones each run at 70% and one fails, the other two must absorb 105% of one zone's load; run at about 60% or use autoscaling headroom.
- **Cross-zone load balancing:** it spreads load evenly regardless of per-zone instance counts but increases cross-zone traffic (billed on most clouds); without it, uneven instance counts cause hot zones.
- **Stateful systems** (databases, queues) need their own replication story: synchronous replicas cost write latency; asynchronous replicas can lose recent writes on failover. State the trade-off and the failover procedure.
- **Health checks and draining** must remove a failing zone's targets quickly, and the application must tolerate dependencies in other zones being 1–2 ms further away.
- **Test it.** Drain or fail a zone in staging (and, with care, in production during a planned exercise) and measure user-visible impact against the stated objective.

**Multi-AZ is not backup.** It protects against zone failure, not against a bad deployment, a deleted table or a compromised credential.

## Cloud connectivity trade-offs

| Option | Connects | Strengths | Limits and costs |
| --- | --- | --- | --- |
| Peering | Two networks | Simple, low latency, no extra device | Non-transitive (A–B and B–C does not give A–C); needs non-overlapping CIDRs; routes on both sides; scales poorly (mesh of N networks) |
| Transit hub (transit gateway or equivalent) | Many networks and sites | Hub-and-spoke routing, central policy and inspection, transitive | Per-attachment and per-GB charges; one more critical component and route-table design to own |
| Private service endpoints (PrivateLink style) | A client network to one *service* | No CIDR overlap problem, no network-wide exposure, one-way access | Per-service; endpoint cost per zone; DNS must point at the endpoint |
| Site-to-site VPN | On-premises or other cloud over the internet | Fast to set up; encrypted; redundant tunnels | Throughput per tunnel limited; internet-dependent latency and jitter; BGP or static routing to maintain |
| Dedicated private link (Direct Connect style) | A site to the cloud over a private circuit | Predictable latency and bandwidth; lower egress cost at volume | Lead time (weeks), cost, a physical single point unless doubled; not encrypted by default |
| Public endpoint + TLS + auth | Anything | Trivial to start | Exposed to the whole internet; needs strong authentication and rate limiting |

Decision heuristics:

- **Few networks, simple topology:** peering. **Many networks or shared inspection:** a transit hub.
- **Exposing one service to many consumers (possibly with overlapping CIDRs):** a private endpoint rather than network-wide connectivity.
- **Hybrid with a business-critical link:** a dedicated link **plus** VPN as backup, tested by actually failing over.
- **Always** plan address space first; overlapping ranges are the most expensive networking mistake to fix after the fact.
- **Cost model:** estimate cross-zone, cross-region, NAT processing and egress charges per GB for the *main data flow*, because a chatty service across a billed boundary can cost more than the instances behind it.

## Failure drills with recovery

For each: baseline, controlled fault, evidence, recovery.

- *Wrong bind:* change a published port from `0.0.0.0:8000` to loopback only; show the service works locally and fails from another machine; show `ss` evidence; restore.
- *Native firewall drop:* drop a port on a host listener; show a timeout; restore. Do this only on a snapshot-able machine.
- *Dependency down:* stop the database; show `/health` 200 and `/ready` 503; restore. Ban "blind restart as the first command": identify the hop before touching anything.
- *Certificate rotation:* replace a server certificate with one that expires in an hour; confirm the expiry alert triggers; renew automatically and confirm clients see the new certificate with no downtime.
- *DNS record failure:* point a test record at an unhealthy address; measure the time from fault to client recovery against the arithmetic in the runbook.
- *Zone loss:* drain one zone; check capacity, error rate and latency.
- *Route removal:* remove a route in a lab network; verify that path analysis and flow logs identify the break before you inspect the table by hand.

## Professional trade-offs

| Decision | Benefit | Cost | When to accept the cost |
| --- | --- | --- | --- |
| Re-encrypt to the application | Encrypted on every link | Two certificate sets; more CPU | Sensitive or regulated data |
| Two DNS providers | Survives a provider outage | Sync complexity; feature differences | Zones whose loss is a total outage |
| Very short DNS TTL | Fast failover | More queries; resolver load; exposure to resolver outages | Only the records you actually fail over |
| NAT per zone | Zone independence | Multiple NAT charges | Any production multi-zone design |
| Strict egress allow-lists | Limits exfiltration | Operational friction when dependencies change | Data-handling services |
| Transit hub | Central policy and transitivity | Cost; single critical component | More than a handful of networks |
| Deep health checks | Fewer bad answers | Risk of ejecting everything when a shared dependency slows | Pair with sensible fail-open limits |
| mTLS everywhere | Strong identity | Issuance and rotation burden | Sensitive east-west traffic |

## Decision guide

| Symptom | Likely hop | First check |
| --- | --- | --- |
| Name not found | DNS | `dig`, resolver in use, search domains |
| Timeout | Route, firewall, security group | `ip route get`, rules, where the path breaks |
| Connection refused | Listener | `ss -ltnp`, bind address, port |
| Certificate error | TLS | Name, chain, dates, clock |
| 5xx with healthy path | Process or dependency | Application logs, `/ready` |
| Works by IP, not by name | DNS | Resolver, record, TTL |
| Works from one zone only | Routing or per-zone resource | Route tables, NAT, security groups of the failing zone |
| Sporadic `502` after idle | Keep-alive mismatch | Backend idle timeout versus balancer |
| Intermittent timeouts at peak | NAT or connection-limit exhaustion | NAT and conntrack metrics |
| After a record change, some users on the old server | Caching | Authoritative versus recursive answers, TTL |

## Knowledge consolidation

- **Design zones and write the flow matrix**; reference identities rather than addresses; test negatives, not only positives.
- **Terminate TLS deliberately**: edge, re-encrypt, pass-through or mTLS is a threat-model decision. Automate issuance and renewal, and alert on expiry long before it matters.
- **DNS is a dependency with no fallback unless you build one**: two name servers in different networks, deliberate TTLs, health-checked failover whose arithmetic you have written down.
- **Routing failures are silent timeouts**; follow the path through route tables, return routes, security groups, ACLs and host rules, using path analysis and flow logs as evidence.
- **Log and probe**: flow logs prove allow/deny, balancer logs prove status, synthetic probes expose the degrading hop.
- **Multi-AZ means one of everything per zone**, with capacity headroom, and still is not a backup.
- **Connectivity choices are trade-offs** of topology, overlap, bandwidth and cost; plan addresses first.
- **Rehearse**: drills turn the runbook from a hope into a measured procedure.

## Exercises

**Exercise 1 — Flow matrix.** For your `orders-api` environment (or a lab one), write the flow matrix with source, destination, port, reason, owner and control. Mark which rows you have *tested*. Add three negative tests and implement one.

**Exercise 2 — TLS decision record.** Write a one-page decision record choosing among edge termination, re-encryption and mTLS for three services handling (a) public catalogue data, (b) customer profiles, (c) payment tokens. State the threat model and the failure mode of the chosen control.

**Exercise 3 — Expiry monitoring.** Implement an external expiry probe for three endpoints, with alerts at 21, 7 and 2 days. Create a test certificate with a lifetime of three days and verify each alert fires.

**Exercise 4 — DNS failover arithmetic.** For a record with TTL 300 and health checks at 30-second intervals requiring 3 failures, compute worst-case failover time. Redesign it to meet a 90-second objective, listing the trade-offs of each change. Then measure actual failover in a lab and compare.

**Exercise 5 — Route break.** In a lab network, remove one route and use flow logs and a path-analysis tool to locate it. Document each diagnostic step and what it ruled out.

**Exercise 6 — Zone drain.** Drain one zone of a three-zone deployment. Record request rate, error rate and latency before, during and after; compute the headroom you actually had.

**Exercise 7 — Connectivity choice.** Given four networks with overlapping `10.0.0.0/16` ranges that need access to one internal API, choose a connectivity option. List alternatives and why you rejected each.

**Exercise 8 — Runbook walkthrough.** Give the runbook to someone who did not write it and have them diagnose a deliberately injected fault. Record where they hesitated and revise the runbook.

**Solution notes.**

*Exercise 1.* Strong answers show every allow rule traceable to a business need and at least one tested negative that actually fails if a rule is loosened. Unowned rules should be flagged for review.

*Exercise 2.* (a) Edge termination is usually enough; (b) re-encryption inside the network; (c) mTLS with workload identity and short-lived certificates. Marks for naming each control's failure mode (for example, an unmonitored internal certificate expiring) and its detection.

*Exercise 3.* Alerts should be generated by the probe independently of the certificate manager, so a failure of renewal automation is still visible. Verify that the 2-day alert pages and the 21-day alert opens a ticket.

*Exercise 4.* Worst case is detection (90 s) plus TTL (300 s) = about 390 s. To reach 90 s you need faster detection (10 s × 3 = 30 s) *and* a TTL of 30–60 s, or, better, a load balancer that fails over in seconds so DNS need not change. Costs: more health-check charges, more queries, still some non-compliant clients.

*Exercise 5.* Expected path: symptom → path analysis names the first blocking component → flow logs show accepted-then-silent → route table inspection confirms. The point is the ordered ruling-out.

*Exercise 6.* With three zones each at utilisation *u*, a failure leaves two zones carrying *1.5u*. Above roughly 66% the remaining zones saturate; your measurements should show where latency starts to climb.

*Exercise 7.* A private endpoint (service exposure) avoids the overlap entirely, because consumers connect to an endpoint address in their own range. Peering and transit fail because routing cannot distinguish overlapping ranges without translation, which is a fragile workaround.

*Exercise 8.* Hesitation marks missing context, unclear commands or assumed access; fix the runbook, not the person.

## Mentoring prompts

Explain how you would prove, to a sceptical security reviewer, that the database zone cannot reach the internet. Why can a single NAT device make a three-zone design effectively single-zone, and how would you discover it in an existing system? Your certificate renewed on schedule, but users still see the old one; list three places the old certificate could be coming from. When would you choose private endpoints over peering, and what would you give up?

---

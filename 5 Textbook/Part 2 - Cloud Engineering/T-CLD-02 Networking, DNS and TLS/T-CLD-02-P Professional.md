# T-CLD-02-P — Professional Engineering

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-p"></a>
#### T-CLD-02-P — Professional Engineering

**An ordered diagnostic method.** Write it down as a runbook so another engineer can follow it:

1. **Name:** resolves? (`dig`, `getent hosts`) from where the client runs.
2. **Route:** does the client have a path? (`ip route get`, traceroute where permitted)
3. **Port:** open? (`nc -vz`, `curl -m`) — refused versus timeout.
4. **TLS:** handshake OK, name and chain valid, not expired?
5. **Process:** answering correctly? (status code, body)
6. **Dependency:** database, queue, downstream API healthy?

State results as evidence ("timed out after 3 s at hop 3 from client subnet A; succeeded from subnet B") rather than conclusions.

**Failure drills with recovery.** For each: baseline, controlled fault, evidence, recovery.

- *Wrong bind:* change a published port from `0.0.0.0:8000` to loopback only; show the service works locally and fails from another machine; show `ss` evidence; restore.
- *Native firewall drop:* drop a port on a host listener; show a timeout; restore. Do this only on a snapshot-able machine.
- *Dependency down:* stop the database; show `/health` 200 and `/ready` 503; restore. Ban "blind restart as the first command": identify the hop before touching anything.

**Where TLS terminates.** Decide and document: at a load balancer (simple certificate management, plaintext inside the private network), at a reverse proxy, at the application, or end to end with mutual TLS between services. Match the decision to your threat model and compliance needs. Local development often uses plain HTTP; production does not.

**Certificate lifecycle.** Automate issuance and renewal (ACME or a cloud certificate manager), monitor expiry with alerts well ahead of the date (for example 21 and 7 days), keep private keys out of source control and images, and test the renewal path.

**Network design vocabulary.**

| Concept | Meaning |
| --- | --- |
| CIDR block | An address range such as `10.50.0.0/16` |
| Subnet | A slice of the range, often tied to one availability zone |
| Public vs private subnet | Whether routes to an internet gateway exist |
| NAT | Lets private instances reach out without being reachable inbound |
| Security group (stateful) | Allow-list firewall attached to interfaces |
| Network ACL (stateless) | Subnet-level allow and deny rules |
| Load balancer | Distributes traffic, terminates TLS, checks health |

**Decision guide**

| Symptom | Likely hop | First check |
| --- | --- | --- |
| Name not found | DNS | `dig`, resolver in use, search domains |
| Timeout | Route, firewall, security group | `ip route get`, rules, where the path breaks |
| Connection refused | Listener | `ss -ltnp`, bind address, port |
| Certificate error | TLS | Name, chain, dates, clock |
| 5xx with healthy path | Process or dependency | Application logs, `/ready` |
| Works by IP, not by name | DNS | Resolver, record, TTL |

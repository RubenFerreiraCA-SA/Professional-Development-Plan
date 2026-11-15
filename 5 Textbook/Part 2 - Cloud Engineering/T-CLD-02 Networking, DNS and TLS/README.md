# T-CLD-02 — Networking, DNS and TLS

*Part 2 — Cloud Engineering*


A request travels through name resolution, routing, a port, an optional encrypted channel, a process and its dependencies. Each hop fails independently and fails differently. The professional skill is to prove *which* hop failed, using ordered tests and written evidence.

## Levels


- [Beginner Foundations](T-CLD-02-B%20Beginner.md#t-cld-02-b) — what a network request does, hosts, IPs, subnets and ports, TCP versus UDP, DNS, HTTP and HTTPS, a browser-to-service trace with timing, refused versus timeout, a failure tour.
- [Intermediate Practice](T-CLD-02-I%20Intermediate.md#t-cld-02-i) — CIDR by hand, longest-prefix routing, NAT, DNS records and caches, the TLS certificate chain with an offline lab, stacked firewalls, load balancers, a `dig`-and-connection diagnosis routine.
- [Professional Engineering](T-CLD-02-P%20Professional.md#t-cld-02-p) — trust zones and flow matrices, TLS termination and identity, certificate lifecycle, DNS resilience, silent routing failures, connectivity logging, multi-AZ design, cloud connectivity trade-offs.
- [Expert Depth](T-CLD-02-E%20Expert.md#t-cld-02-e) — hybrid and multi-region networks, zero-trust identity, traffic engineering, partial failure, DNS and TLS incident patterns, security versus availability, migrations without outages.

All examples use a neutral `orders-api` service at `orders.example.com` with documentation and private address ranges; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results; case studies are composites.

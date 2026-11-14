# T-CLD-02-B — Beginner Foundations

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-b"></a>
#### T-CLD-02-B — Beginner Foundations

**The reachability path.**

```text
client → DNS name resolution → route to the address → port reachable → TLS handshake → process answers → dependency answers
```

Label which hop you are testing in every note. A failure at one hop makes later hops untestable, so test in order.

**Addresses, ports and protocols.** An IP address identifies a network interface; a port identifies a service on it; TCP provides a reliable stream; HTTP runs over TCP (and HTTPS is HTTP over TLS over TCP). `127.0.0.1` ("localhost") always means *this machine* — from inside a container, that is the container itself.

**First commands**

```bash
ip -br a                   # interfaces and addresses
ip route                   # default gateway and connected networks
ip route get 93.184.216.34 # which path would be used for this address?
getent hosts example.com   # name resolution as the system sees it
dig +short example.com     # ask DNS directly
curl -sv http://127.0.0.1:8000/health -o /dev/null
nc -vz 127.0.0.1 8000      # is the TCP port open?
```

**Connection refused versus timeout.** *Refused* usually means the host answered but nothing is listening (process down or wrong port). A *timeout* usually means packets are being dropped or lost (firewall, security group, routing). This distinction is extremely informative.

**Health versus readiness.** `/health` says "the process is up". `/ready` says "its dependencies work". If `/health` is 200 and `/ready` is 503, the network path to the service is fine; the *dependency* hop is failing.

**Worked example: "the API is down".** A colleague says `orders-api` is unreachable. Walk the path in order and stop at the first failing hop:

| Hop | Command | Healthy result | What a failure suggests |
| --- | --- | --- | --- |
| Name | `getent hosts orders.example.com` | One or more addresses | Empty output: DNS record missing, typo, or wrong resolver. |
| Route | `ip route get <address>` | A line naming a gateway or device | `RTNETLINK answers: Network is unreachable`: no route; check the default gateway or VPN. |
| Port | `nc -vz <address> 443` | `succeeded` | *Refused*: nothing listening or wrong port. *Timeout*: dropped by a firewall, security group or route. |
| TLS | `curl -sv https://orders.example.com/ -o /dev/null` | Handshake completes, certificate subject matches | Certificate or handshake error: expired, wrong name or untrusted chain (details in the Intermediate level). |
| Process | `curl -s -o /dev/null -w '%{http_code}\n' https://orders.example.com/health` | `200` | `502`/`503`/`504` from a proxy: the front door works but the backend does not. |
| Dependency | `curl -s https://orders.example.com/ready` | `200` | `503` with `/health` at 200: process is fine, dependency hop failing. |

**Reading the first commands.**

```text
$ ip -br a
lo      UNKNOWN  127.0.0.1/8
eth0    UP       10.0.1.15/24
$ ip route get 93.184.216.34
93.184.216.34 via 10.0.1.1 dev eth0 src 10.0.1.15
$ getent hosts example.com
2606:2800:...  example.com
$ dig +short example.com
93.184.216.34
```

`eth0` has the address `10.0.1.15`; traffic to an outside address leaves via gateway `10.0.1.1`. `getent` asks the operating system's resolver (hosts file, resolver settings) while `dig` asks a DNS server directly; if they disagree, the host's own configuration is overriding DNS.

**Why `127.0.0.1` surprises people in containers.** Each container has its own network namespace. If `orders-api` is configured with `DB_HOST=127.0.0.1`, it looks for a database inside its own container, finds nothing and gets *connection refused*, even though the database runs happily elsewhere. The fix is to use the database's service name or address. The mirror image also bites: a server bound only to `127.0.0.1` inside a container cannot be reached from outside it; bind to `0.0.0.0`.

**Common mistakes**

- Testing with `ping` and concluding the service is down. Many networks block ICMP, and ping says nothing about a port.
- Changing several things at once, then not knowing which one fixed it.
- Treating *every* failure as "DNS". Prove the name resolves before blaming it.
- Reading `HTTP 200` from `/health` as proof that users can place orders; that is what `/ready` and a real request are for.

**Diagram to draw.** One horizontal line of boxes (client, DNS, route, port, TLS, process, dependency), each labelled with its test command and last result, with the failing box circled.

**Exercise.** Run a local service. Show: it answers; stop it and show *connection refused*; use a firewall rule or a wrong port to show a different symptom. Write one sentence per symptom naming the failing hop.

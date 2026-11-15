# T-CLD-02-B — Beginner Foundations

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-b"></a>
#### T-CLD-02-B — Beginner Foundations

## Why this matters

Almost every outage report starts with "the service is down." That sentence hides a chain of independent steps. Before a byte of an order reaches `orders-api`, a name must become an address, a path must exist, a port must accept a connection, an encrypted channel must be agreed, and only then does a process run code. Each step fails alone, with its own signature.

The beginner skill is saying, with evidence, **which step failed** — before changing anything.

This section assumes a Linux or macOS terminal and no networking background. Examples use a fictional `orders-api` at `orders.example.com`, with addresses from documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) and private ranges. Outputs marked *illustrative* show shape, not measurements.

## First principles: what a network request actually is

A computer cannot send "a request to orders.example.com". Hardware and operating systems only know how to do a much smaller set of things:

1. Put bytes into a **packet** that carries a destination **IP address**.
2. Hand the packet to the next machine (a **router**) that is closer to that address.
3. Repeat until a machine recognises the address as its own.
4. Deliver the payload to a **process** on that machine, selected by a **port number**.

Everything else — names, encryption, web pages — is built on top of those four moves. Analogy, and its limit: a packet is a parcel with a street address (IP) and a flat number (port), passed from depot to depot. Unlike parcels, packets are dropped routinely; the software at the ends notices and resends.

### Layers: an envelope inside an envelope

Networking software is organised in layers; each layer wraps the one above it with its own header, like putting a letter in an envelope and the envelope in a courier bag.

```text
HTTP message          what is being asked        (GET /orders/42)
  inside TLS record   privacy and identity       (encrypted)
    inside TCP segment  which process, reliable    (ports, sequence numbers)
      inside IP packet    which machine            (source and destination IP)
        inside frame        next hop, locally      (Ethernet / Wi-Fi)
```

Two consequences: a router reads only the network layer and does not care that your payload is HTTP; and a port-filtering firewall works at the transport layer, so "the port is blocked" and "the route is missing" are different problems with different symptoms.

## Hosts, IP addresses, subnets and ports

**A host** is anything with a network interface (laptop, server, container, VM). **An IPv4 address** is 32 bits written as four decimal *octets* between 0 and 255, such as `10.0.1.15`; **IPv6** addresses are 128 bits in hexadecimal groups (`2001:db8::15`). The ideas are identical; examples here use IPv4.

**Public and private ranges.** Three IPv4 blocks are private and never routed on the public internet: `10.0.0.0/8`, `172.16.0.0/12` and `192.168.0.0/16`. Home routers, offices and cloud private networks all use them, so two companies can both have `10.0.1.15`. Also recognise `127.0.0.0/8` (loopback: *this machine*), `169.254.0.0/16` (self-assigned link-local, often a sign DHCP failed) and `0.0.0.0` ("all interfaces" when listening).

**A subnet** is a group of addresses that are reachable directly, without going through a router. The notation `10.0.1.15/24` means "address `10.0.1.15` on a network whose first 24 bits are the network part". The `/24` is the *prefix length*. The remaining 8 bits identify hosts within that network, so a `/24` holds 256 addresses (`10.0.1.0` to `10.0.1.255`). Later levels teach you to do this arithmetic by hand; for now, keep one rule: **a machine talks directly to addresses inside its subnet and sends everything else to its default gateway.**

```text
Your host:      10.0.1.15/24     → local network is 10.0.1.0 – 10.0.1.255
Destination A:  10.0.1.40        → inside the subnet: send directly
Destination B:  203.0.113.10     → outside: send to the gateway, 10.0.1.1
```

**A port** is a 16-bit number (0–65535) that tells the destination machine which process should receive the data. Well-known ports include 22 (SSH), 53 (DNS), 80 (HTTP) and 443 (HTTPS). A **socket** is the combination of an address, a port and a protocol; a **connection** is identified by *four* values — source address, source port, destination address, destination port — which is how a server tells apart thousands of clients all connecting to its port 443. When your machine opens a connection it picks a random *ephemeral* source port (on Linux usually between 32768 and 60999).

**A listener** is a process that has asked the operating system to deliver connections arriving at a given address and port to it. If no listener exists, the operating system answers an incoming connection attempt with a refusal. Which address the listener is *bound* to matters:

- Bound to `127.0.0.1:8000`: reachable only from this machine or container.
- Bound to `0.0.0.0:8000`: reachable on every interface of this machine.
- Bound to `10.0.1.15:8000`: reachable only through that interface's address.

Check with `ss`:

```bash
ss -ltnp          # listening TCP sockets, numeric, with owning process
```

```text
State   Local Address:Port  Process
LISTEN  127.0.0.1:8000      users:(("python3",pid=2104,fd=3))
LISTEN  0.0.0.0:22          users:(("sshd",pid=801,fd=3))
```

Here `python3` listens only on loopback. Anyone on another machine will get a refusal even though the service is "running".

## TCP, UDP and what "reliable" means

**TCP** (Transmission Control Protocol) gives two programs a reliable, ordered stream of bytes. It does this by numbering bytes, acknowledging them, resending what is lost and slowing down if the network is congested. Before data flows, the two sides perform the **three-way handshake**:

```text
client                                    server (listening on :443)
  | ---- SYN  (seq=x) ------------------->  |   "I would like to connect"
  | <--- SYN-ACK (seq=y, ack=x+1) --------  |   "Agreed; here is my starting number"
  | ---- ACK  (ack=y+1) ------------------> |   "Received; connection established"
  | ---- data ... ------------------------> |
```

When the client's `SYN` arrives at a machine with *no* listener, the operating system replies with a `RST` (reset): the client sees **connection refused** within milliseconds. When a firewall silently drops the `SYN`, nothing comes back; the client retransmits after 1 s, 2 s, 4 s and so on until it gives up, and the user sees a **timeout**. This one fact — *a refusal is an answer, a timeout is silence* — is the single most useful diagnostic in the chapter.

**UDP** (User Datagram Protocol) sends individual datagrams with no handshake, no retransmission and no ordering. It suits cases where the application handles loss or a late answer is useless: DNS queries, video calls and (as QUIC) HTTP/3.

"Reliable" does not mean "always works". It means TCP *tells you* when it could not deliver, after retrying, by timing out or resetting. An application that ignores that signal or waits forever is a classic source of hangs (a topic for the Professional level).

## DNS: turning names into addresses

People use names; networks use addresses. The **Domain Name System** is a distributed, hierarchical database that maps one to the other. A name is read right to left: in `orders.example.com`, `com` is the top-level domain, `example` is a domain registered under it and `orders` is a label inside that domain. Each level is managed by someone different, who runs (or pays someone to run) **authoritative name servers** for it.

Your program never walks that hierarchy itself. It asks a **recursive resolver** (provided by your network, your ISP, your cloud platform or a public service) to do it:

```text
your program ──► OS resolver / cache ──► recursive resolver ──► root servers      ("who knows .com?")
                                                          ├──► .com servers      ("who knows example.com?")
                                                          └──► example.com's authoritative server
                                                                ("orders.example.com is 203.0.113.10")
```

The answer is cached at several levels for a time given in the record, the **TTL** (time to live) in seconds. A TTL of 300 means "reuse this answer for up to five minutes". Caching makes DNS fast and cheap; it also means a change you make does not appear everywhere at once.

The record types you will meet first:

| Record | Meaning | Example |
| --- | --- | --- |
| `A` | Name → IPv4 address | `orders.example.com. 300 IN A 203.0.113.10` |
| `AAAA` | Name → IPv6 address | `orders.example.com. 300 IN AAAA 2001:db8::10` |
| `CNAME` | This name is an alias for another name | `www.example.com. 300 IN CNAME orders.example.com.` |

Ask DNS directly with `dig`:

```bash
dig orders.example.com A
```

```text
;; ANSWER SECTION:
orders.example.com.   247   IN   A   203.0.113.10

;; Query time: 31 msec
;; SERVER: 10.0.1.1#53(10.0.1.1) (UDP)
```

Read it: the answer is `203.0.113.10`; it may be cached for 247 more seconds (the TTL counts down as the resolver's cache ages — a second run showing a lower TTL proves a cache); the question went to `10.0.1.1` port 53 over UDP and took 31 ms.

`dig` and the system's own lookup can disagree: programs use the operating system's resolver, which consults the **hosts file** (`/etc/hosts`) before DNS (order set in `/etc/nsswitch.conf`). `getent hosts name` shows what programs actually see.

## HTTP and HTTPS in one page

**HTTP** is a text-based request/response protocol. A client sends a request line, headers and optionally a body; the server replies with a status line, headers and a body.

```text
GET /orders/42 HTTP/1.1
Host: orders.example.com
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 58

{"id": 42, "status": "shipped", "items": 3}
```

The `Host` header matters: many sites share one IP address, and the server (or a load balancer in front of it) uses `Host` to decide which site you meant.

Status codes group by first digit: 2xx success, 3xx redirect, 4xx the *request* was wrong (`401` not authenticated, `403` forbidden, `404` not found, `429` too many requests), 5xx the *server* failed. For diagnosis, 502/503/504 are especially informative: they are usually produced by a **proxy or load balancer** in front of your service, and they mean "I am alive, but I could not get a good answer from the thing behind me". The front door works; the backend does not.

**HTTPS** is HTTP carried inside **TLS** (Transport Layer Security). TLS gives three things: the traffic is *encrypted* (eavesdroppers see noise), *authenticated* (the server proves it is really `orders.example.com`, using a certificate signed by an authority your computer trusts) and *integrity-protected* (tampering is detected). The Intermediate level takes certificates apart. For now, the key points: HTTPS adds a handshake between the TCP handshake and the first HTTP request; the browser's padlock only means "the server holds a valid certificate for this name" — it says nothing about whether the site is honest; and a certificate problem produces a *different* error from a network problem, because the TCP connection succeeded first.

## The browser-to-service trace

Here is what happens when you type `https://orders.example.com/orders/42` into a browser, in order. Each numbered stage is a hop you can test separately.

```text
1  Parse URL            scheme=https host=orders.example.com port=443 path=/orders/42
2  Local shortcuts      browser DNS cache? hosts file? HSTS rule? connection already open?
3  DNS resolution       name → 203.0.113.10                          [UDP 53]
4  Routing decision     203.0.113.10 is outside my subnet → send via default gateway
5  Local delivery       find the gateway's hardware address (ARP), send an Ethernet frame to it
6  Hops across the net  each router decrements TTL, picks the next hop; home router rewrites
                        the source address (NAT); the packet arrives at 203.0.113.10
7  TCP handshake        SYN → SYN-ACK → ACK to port 443               [1 round trip]
8  TLS handshake        hello, certificate, key agreement             [1 more round trip on TLS 1.3]
9  HTTP request         GET /orders/42  (encrypted inside TLS)
10 Server side          load balancer → app process → database → response built
11 HTTP response        200 OK + body, back along the same connection
12 Reuse or close       the connection often stays open for the next request
```

**Stages 4–6: routing, ARP, hops and NAT.** Your machine compares the destination with its routing table; `203.0.113.10` is outside `10.0.1.0/24`, so it uses the default gateway `10.0.1.1`. It learns the gateway's hardware address by broadcasting an **ARP** request and caching the reply. The packet's destination IP never changes en route; only the frame's next-hop address does. Each router decrements the packet's *time to live* (TTL) and discards it at zero — which is what `traceroute` exploits. At the network edge, **NAT** rewrites the private source address to a public one and remembers the mapping so replies return.

**Stages 7–8: why connections are expensive.** A fresh HTTPS connection costs one round trip for TCP plus one or two for TLS before the first HTTP byte. At 100 ms distance that is 200–300 ms of set-up, which is why clients **reuse connections** (keep-alive).

You can measure the early stages with one command:

```bash
curl -s -o /dev/null \
  -w 'dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s first_byte=%{time_starttransfer}s total=%{time_total}s\n' \
  https://orders.example.com/orders/42
```

```text
dns=0.031s connect=0.062s tls=0.118s first_byte=0.171s total=0.173s
```

The numbers are cumulative from the start of the request. Subtract to get stage costs: DNS took 31 ms; TCP connect finished at 62 ms (31 ms of its own — one round trip); TLS finished at 118 ms (56 ms of handshake); the server needed another 53 ms before the first byte. If `dns` is huge, look at resolvers; if `connect` is huge, look at the path; if `tls` is huge, look at the handshake and the certificate chain; if `first_byte` is huge, the problem is in the application, not the network.

## The reachability path

Compress the trace into a checklist:

```text
client → DNS name resolution → route to the address → port reachable → TLS handshake → process answers → dependency answers
```

Name the hop in every note; later hops are untestable after a failure.

**Connection refused versus timeout.** *Refused* usually means the host answered but nothing is listening (process down or wrong port). A *timeout* usually means packets are being dropped or lost (firewall, security group, routing). This distinction is extremely informative.

**Health versus readiness.** `/health`: the process is up. `/ready`: its dependencies work. If `/health` is 200 and `/ready` is 503, the network path to the service is fine; the *dependency* hop is failing.

**Worked example: "the API is down".** A colleague says `orders-api` is unreachable. Walk the path in order and stop at the first failing hop:

| Hop | Command | Healthy result | What a failure suggests |
| --- | --- | --- | --- |
| Name | `getent hosts orders.example.com` | One or more addresses | Empty output: DNS record missing, typo, or wrong resolver. |
| Route | `ip route get <address>` | A line naming a gateway or device | `RTNETLINK answers: Network is unreachable`: no route; check the default gateway or VPN. |
| Port | `nc -vz <address> 443` | `succeeded` | *Refused*: nothing listening or wrong port. *Timeout*: dropped by a firewall, security group or route. |
| TLS | `curl -sv https://orders.example.com/ -o /dev/null` | Handshake completes, certificate subject matches | Certificate or handshake error: expired, wrong name or untrusted chain (details in the Intermediate level). |
| Process | `curl -s -o /dev/null -w '%{http_code}\n' https://orders.example.com/health` | `200` | `502`/`503`/`504` from a proxy: the front door works but the backend does not. |
| Dependency | `curl -s https://orders.example.com/ready` | `200` | `503` with `/health` at 200: process is fine, dependency hop failing. |

## Worked failure tour: five symptoms, five hops

Run a tiny service so you can break it safely:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 &   # serves the current directory on loopback
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/     # 200
```

| You do | You see | Why | Failing hop |
| --- | --- | --- | --- |
| `kill %1`, then `curl -sv http://127.0.0.1:8000/` | `Failed to connect ... Connection refused` immediately | The `SYN` met no listener; the OS replied with a reset | Port / process |
| `curl -sv http://127.0.0.1:8001/` | The same refusal | Wrong port: still nothing listening there | Port (client configuration) |
| `curl -sv http://no-such-name.invalid/` | `Could not resolve host` | The name never became an address; no packet was sent to any server | Name |
| `curl -m 3 -sv http://10.255.255.1/` (an unused private address) | `Connection timed out after 3001 milliseconds` | `SYN` went out, nothing came back | Route / filter (silence) |
| Start the server on `127.0.0.1`, then `curl http://<your-LAN-address>:8000/` | Refused | Listening on loopback only; the LAN address has no listener | Bind address |

Note that **three of the five say "refused"** while meaning different causes, so confirm with `ss -ltnp` rather than guessing. Only the first message points at DNS.

**Why `127.0.0.1` surprises people in containers.** Each container has its own network namespace. If `orders-api` is configured with `DB_HOST=127.0.0.1`, it looks for a database inside its own container, finds nothing and gets *connection refused*, even though the database runs happily elsewhere. The fix is to use the database's service name or address. The mirror image also bites: a server bound only to `127.0.0.1` inside a container cannot be reached from outside it; bind to `0.0.0.0`.

## Safe habits

- Write down the hop and the command: "Hop 3, `nc -vz 203.0.113.10 443`, timed out after 3 s, from the office network."
- Change one thing at a time; undo it if it did not help.
- Do not disable certificate checks (`curl -k`) to "see if it works"; it removes the check you are trying to observe.

**Common mistakes**

- Concluding "down" from `ping`: many networks block ICMP, and ping says nothing about a port.
- Blaming "DNS" for everything; prove the name resolves first.
- Reading `HTTP 200` from `/health` as proof that users can place orders; that is what `/ready` and a real request are for.
**Diagram to draw.** A horizontal line of boxes (client, DNS, route, port, TLS, process, dependency), each labelled with its test command and result, the failing box circled.

## Knowledge consolidation

- A request is a *chain* of independent hops: name, route, port, TLS, process, dependency. Test them **in order** and name the hop in every note.
- An IP address identifies an interface, a port identifies a process, a **connection** is identified by four values (two addresses, two ports). A subnet is the set of addresses you can reach without a router.
- `127.0.0.1` is *this* machine — and from inside a container, *that container*. A listener bound to loopback is invisible from outside.
- **A refusal is an answer; a timeout is silence.** Refusal: host reachable, nothing listens. Timeout: packets lost or filtered.
- HTTPS is HTTP inside TLS; certificate errors are a different class of failure from network errors because TCP already succeeded.
- 502/503/504 usually mean a proxy is alive and its backend is not; `/health` and `/ready` separate process from dependency. `curl -w` splits time into DNS, connect, TLS and first byte.

## Exercises

**Exercise 1 — Trace your own request.** Pick a public website. Using only `dig`, `ip route get`, `nc -vz` and `curl -v`, write down for each of the stages in the trace: the command, the output and a one-line interpretation. Include certificate subject and expiry.

**Exercise 2 — Refused versus timeout.** With the local `http.server` from the failure tour, produce a refusal (stop the server) and a timeout (use `nc` or `curl -m 3` toward an unused private address, or a firewall rule on a disposable machine). Write one sentence each naming the failing hop and the next check.

**Exercise 3 — Subnet reading.** For each of `10.0.1.15/24`, `192.168.0.77/24`, `10.0.1.200/25` and `172.16.5.9/16`, state which of `10.0.1.40`, `10.0.1.220`, `192.168.0.250` and `172.16.200.1` are in the same subnet (answers in the solution notes; Intermediate teaches the arithmetic).

**Exercise 4 — Container localhost.** Run two containers on a user-defined network, one serving HTTP and one calling it. Configure the caller with `127.0.0.1`, then with the service name; record the error and explain it using network namespaces.

**Solution notes.**

*Exercise 1.* A good answer shows: a name→address line (`dig +short`), a route line naming the gateway and interface, a `succeeded` from `nc`, the `Subject`, `Issuer` and `notAfter` lines from `curl -v` or `openssl s_client`, and a status code. The interpretation should say what would look different if each stage failed.

*Exercise 2.* Stopping the server gives an immediate `Connection refused`; the unused address gives a timeout after your `-m` value. The refusal's next check is the listener (`ss -ltnp`, process state); the timeout's is the path (route, filter).

*Exercise 3.* `10.0.1.15/24` → network `10.0.1.0/24`: `10.0.1.40` same, `10.0.1.220` same, others different. `192.168.0.77/24` → `192.168.0.250` same. `10.0.1.200/25` → network `10.0.1.128/25` (`.128`–`.255`): `10.0.1.220` same, `10.0.1.40` *different*. `172.16.5.9/16` → `172.16.200.1` same (a /16 fixes only the first two octets).

*Exercise 4.* `Connection refused` to `127.0.0.1` inside the caller: it is its own namespace with no listener. The service name works because user-defined networks provide name resolution.

## Mentoring prompts

Explain why "connection refused" is better news than "connection timed out". Given "the site is slow", which `curl -w` command do you run first and why? What does a browser padlock promise, and what does it not?

---

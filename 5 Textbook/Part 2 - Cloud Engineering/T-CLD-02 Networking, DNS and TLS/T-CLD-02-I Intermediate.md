# T-CLD-02-I — Intermediate Practice

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-i"></a>
#### T-CLD-02-I — Intermediate Practice

## Why this matters

At the Beginner level you walked a request hop by hop and named the failing hop. At this level you learn the machinery inside each hop well enough to *predict* what a command will show before you run it: which addresses a prefix covers, which route wins, what NAT does to a source address, which cache is serving an old DNS answer, which certificate in a chain is wrong, and which layer of filtering dropped a packet. Prediction is the test of understanding; a surprising output is a finding, not an annoyance.

Examples continue with `orders-api` at `orders.example.com`, using private and documentation ranges; lab commands are for machines you own.

## CIDR by hand

An IPv4 address is 32 bits. **CIDR notation** `a.b.c.d/n` says the first `n` bits are the *network part* and the remaining `32 − n` are the *host part*. Everything you need follows from three facts:

1. A `/n` block holds \(2^{32-n}\) addresses.
2. The block starts at an address whose host bits are all zero, and its size is a power of two, so blocks are aligned on multiples of their size.
3. The *mask* is the `n` leading ones: `/24` = `255.255.255.0`, `/22` = `255.255.252.0`, `/20` = `255.255.240.0`.

| Prefix | Addresses | Mask | Block size in the interesting octet |
| --- | --- | --- | --- |
| `/20` | 4,096 | `255.255.240.0` | 16 in the 3rd octet |
| `/22` | 1,024 | `255.255.252.0` | 4 in the 3rd octet |
| `/24` | 256 | `255.255.255.0` | 1 in the 3rd octet |
| `/26` | 64 | `255.255.255.192` | 64 in the 4th octet |
| `/27` | 32 | `255.255.255.224` | 32 in the 4th octet |

**Shortcut.** Find the octet where the mask is neither 255 nor 0. The block size is `256 − mask value` in that octet. The network address is the largest multiple of the block size that does not exceed the address's octet; the broadcast (last) address is the next multiple minus one.

**Worked example 1 — `10.50.8.77/22`.** Mask `255.255.252.0`; the interesting octet is the third; block size `256 − 252 = 4`. The third octet is 8, a multiple of 4, so the network is `10.50.8.0`. The block spans third octets 8–11: last address `10.50.11.255`. Usable hosts in a traditional subnet: `10.50.8.1`–`10.50.11.254` (1,022). Check in binary: third octet `8 = 00001000`; mask `252 = 11111100`; AND gives `00001000 = 8`. ✓

**Worked example 2 — `172.16.37.200/21`.** Mask `255.255.248.0`; block size 8 in the third octet. Largest multiple of 8 not exceeding 37 is 32. Network `172.16.32.0`, last address `172.16.39.255`. Is `172.16.40.5` inside? 40 is past 39, so no.

**Worked example 3 — `192.168.1.100/27`.** Block size `256 − 224 = 32` in the fourth octet. Multiples of 32: 96, 128. Network `192.168.1.96`, last `192.168.1.127`, 30 usable hosts (`.97`–`.126`).

**Splitting a block.** To carve `10.50.0.0/16` into per-zone subnets, each `/20` (4,096 addresses) is 16 apart in the third octet:

```text
10.50.0.0/20     10.50.0.0   – 10.50.15.255    zone a, private
10.50.16.0/20    10.50.16.0  – 10.50.31.255    zone b, private
10.50.32.0/20    10.50.32.0  – 10.50.47.255    zone c, private
10.50.240.0/24   10.50.240.0 – 10.50.240.255   public subnet, zone a
10.50.241.0/24   10.50.241.0 – 10.50.241.255   public subnet, zone b
```

**Overlap test.** CIDR blocks either nest or are disjoint: `10.50.0.0/16` contains `10.50.128.0/17` and is disjoint from `10.51.0.0/16`. If two networks both use `10.0.0.0/16`, a router cannot tell which one `10.0.4.9` means, so choose non-overlapping ranges *before* connecting networks and keep a register.

**Cloud caveat.** Cloud providers reserve a few addresses per subnet. In AWS, five per subnet (the first four and the last), so a `/28` yields 11 usable addresses, not 14. A `/24` private subnet holding 200 autoscaled instances plus load-balancer interfaces and container networking can run out sooner than expected. Size for growth, not today.

## Routing decisions

Every packet-forwarding machine, including your laptop, consults a **routing table**: a list of `(prefix → next hop, interface)` entries. The rule is **longest prefix match**: among entries whose prefix contains the destination, the one with the *longest* prefix (most specific) wins.

```text
$ ip route
default via 10.50.0.1 dev eth0
10.50.0.0/20 dev eth0 proto kernel scope link src 10.50.0.15
10.60.0.0/16 via 10.50.0.254 dev eth0
10.60.8.0/24 dev tun0
```

| Destination | Matching entries | Winner | Why |
| --- | --- | --- | --- |
| `10.50.3.9` | `default`, `10.50.0.0/20` | `10.50.0.0/20` | Connected network; send directly |
| `10.60.2.5` | `default`, `10.60.0.0/16` | `10.60.0.0/16` | Longer than default; via `10.50.0.254` |
| `10.60.8.20` | `default`, `10.60.0.0/16`, `10.60.8.0/24` | `10.60.8.0/24` | Longest prefix; leaves via `tun0` |
| `203.0.113.10` | `default` | `default` | Nothing else matches |

Confirm predictions with `ip route get 10.60.8.20`. If no entry matches and there is no default, the command reports `Network is unreachable`.

**Routing in the cloud.** The same idea, expressed as *route tables* attached to subnets. A subnet is "public" because its table has a route `0.0.0.0/0 → internet gateway`; "private" because its default route points at a NAT device or nowhere. The `local` route for the network's own CIDR is implicit, so every instance can reach every other subnet in the network unless a firewall says otherwise. Debugging a cloud timeout therefore starts with: *which route table does the source subnet use, and does it contain a route for the destination?* — including the **return** path, because replies must also find their way back.

**Asymmetric routing.** If a reply leaves through a different gateway than the request arrived by, stateful devices see half a conversation and drop it: `SYN` seen, `SYN-ACK` sent, connection hangs.

## NAT: what it rewrites and what it remembers

**NAT** (network address translation) rewrites addresses in packets as they pass through a gateway.

| Kind | Rewrites | Used for |
| --- | --- | --- |
| Source NAT (SNAT / masquerade) | The *source* address (and port) of outbound packets | Many private hosts share one public address |
| Destination NAT (DNAT / port forwarding) | The *destination* address (and port) of inbound packets | Publishing an internal service on a public address |

A SNAT gateway keeps a **translation table** (conntrack) so replies can be mapped back:

```text
inside (private)        translated (public)         destination
10.50.0.15:51234   →   198.51.100.7:40001   →   203.0.113.10:443
10.50.0.16:51234   →   198.51.100.7:40002   →   203.0.113.10:443
```

Two private hosts used the same source port, so the gateway assigned different public ports to tell them apart. The table is finite and entries expire after an idle period; consequences you will meet at Professional and Expert levels include port exhaustion and mysterious resets on long-idle connections.

Implications to learn now:

- **Inbound is impossible without a mapping.** A private instance behind SNAT can start connections outward; nobody outside can start one inward. That is the feature.
- **The destination sees the gateway, not the client.** Allow-lists and logs on the far side show the NAT address; your own logs show the private one. Correlate by time and port.
- **IPv6 normally needs no NAT**, so "private by default" rests on firewalls and routes.

## DNS in depth

### The resolution chain and its caches

```text
application cache ─► OS / stub resolver ─► (node-local cache) ─► recursive resolver ─► authoritative servers
   (browser, JVM)     /etc/resolv.conf        (systemd-resolved,      (VPC resolver,        (the zone's own
                      nsswitch + hosts         dnsmasq, CoreDNS)       ISP, public)          name servers)
```

Every box can cache. That is why "I changed the record, but my machine still gets the old answer" is common and not mysterious: the answer may be held in the browser, in a language runtime, in the stub resolver, or in the recursive resolver, each for its own duration. Stub-resolver configuration lives in `/etc/resolv.conf` (on many modern Linux systems pointing at a local `127.0.0.53` stub; use `resolvectl status` to see the real upstream) and contains `nameserver` lines plus `search` domains and options.

### Records you must know

| Record | Purpose | Notes |
| --- | --- | --- |
| `A` / `AAAA` | Name → IPv4 / IPv6 address | A name can have several; clients try them in some order |
| `CNAME` | Alias to another name | Cannot coexist with other records at the same name; cannot sit at the zone apex |
| `MX` | Mail routing, with priority | Points at names, not addresses |
| `TXT` | Arbitrary text | Domain verification, SPF, DKIM, DMARC |
| `NS` | Delegation to name servers | Defines who is authoritative for a zone |
| `SOA` | Zone metadata and negative-caching time | One per zone |
| `SRV` | Service location: host, port, priority, weight | Used by some protocols and service discovery |
| `CAA` | Which CAs may issue for the domain | Checked by CAs at issuance |
| `PTR` | Address → name (reverse DNS) | Lives in `in-addr.arpa` |

Providers add non-standard "alias" records (e.g. Route 53 alias) so an apex name can point at a load balancer, which a plain `CNAME` cannot.

### Asking the right server

```bash
dig orders.example.com A +noall +answer          # just the answer lines
dig orders.example.com AAAA +short
dig example.com NS +short                        # who is authoritative
dig @ns1.example-dns.net orders.example.com A    # ask an authoritative server directly
dig @10.50.0.2 orders.example.com                # ask the cloud's resolver
dig +trace orders.example.com                    # walk delegation from the root
dig -x 203.0.113.10                              # reverse lookup
```

The flags section of a full `dig` answer is informative:

```text
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
```

`aa` (authoritative answer) is present only when an authoritative server answered; `ra` means the server offers recursion; `rd` means you asked for it. Asking an authoritative server directly shows *what the zone says now*; asking a recursive resolver shows *what the world will see, subject to caches*. When those differ, you have found your propagation delay.

**Response codes** tell you more than the data:

| Status | Meaning | Typical cause |
| --- | --- | --- |
| `NOERROR` with answer | Success | — |
| `NOERROR` with empty answer ("NODATA") | The name exists, but not with that record type | Asked for `AAAA` where only `A` exists |
| `NXDOMAIN` | The name does not exist | Typo, record missing, wrong zone |
| `SERVFAIL` | The resolver could not get an answer | Broken delegation, unreachable authoritative servers, DNSSEC validation failure |
| `REFUSED` | The server declines to answer you | Querying a resolver that only serves its own clients |

### TTLs and caching in practice

An answer is cached for its TTL. The remaining TTL in a resolver's answer counts down, so repeated queries show it falling; an authoritative server shows the full value. **Negative answers are cached too**, for the time given in the zone's SOA record (the smaller of its minimum field and the SOA TTL); so a lookup for a name *before* you create the record can keep failing for minutes after you create it.

Planned change procedure: lower the TTL (for example from 3600 to 60) **at least one old-TTL ahead of the change**; make the change; verify with an authoritative query and then a recursive one; keep the low TTL until stable; raise it again. Lowering the TTL at the moment of change helps nobody, because resolvers already hold the old answer with the old TTL.

Not everything honours TTLs: some applications cache lookups for the process lifetime. When a change "has not propagated", find which layer holds the answer before blaming the provider.

**Host DNS is not container DNS.** A name like `db` may resolve inside a user-defined container network (an embedded resolver answers) and not on the host. Always test from where the client runs.

## Ports, listeners and firewalls

A service bound to `127.0.0.1:8000` answers only locally; bound to `0.0.0.0:8000` it answers on all interfaces. A frequent "firewall problem" is actually a loopback-only bind. Check with `ss -ltnp` before touching any rule.

Filtering happens at several independent places; a packet must pass **all** of them:

| Layer | Examples | State | Where evaluated |
| --- | --- | --- | --- |
| Cloud security group | Allow-list attached to an interface | Stateful: replies allowed automatically | Virtual network, before the host |
| Network ACL | Subnet-level numbered allow/deny rules | Stateless: return traffic needs its own rule | At the subnet boundary |
| Host firewall | `nftables`, `iptables`, `ufw` | Usually stateful | In the host kernel |
| Container or cluster policy | Publish rules, network policy | Varies | Bridge or CNI layer |
| Application | Bind address, allow-lists, authentication | — | In the process |

A **stateful** filter remembers an allowed outbound connection and permits its replies. A **stateless** filter judges each packet alone, so for a client connecting to your server on 443 you must allow inbound 443 **and** outbound replies to the client's ephemeral port (1024–65535, to be safe). Forgetting the return rule on a stateless ACL gives a timeout that looks exactly like a blocked port.

Test one change at a time on a disposable machine you can snapshot:

```bash
sudo nft add table inet lab
sudo nft add chain inet lab input '{ type filter hook input priority 0; }'
sudo nft add rule inet lab input tcp dport 18080 drop
curl -m 3 http://<host>:18080/      # expect a timeout, not "refused"
sudo nft delete table inet lab      # recover
```

Change `drop` to `reject with tcp reset` and the symptom becomes an immediate refusal: the *rule's action* decides which signature you see. This is why "timeout versus refused" suggests but does not prove a cause.

Container-published ports are translated by rules in a bridge network and evaluated in forwarding chains, so a simple input-chain drop may not block them. Use cloud security groups, the container platform's rules or network policies for those.

## TLS: the certificate chain

TLS provides encryption, server authentication and integrity. Authentication rests on certificates: a signed statement binding a **name** to a **public key**.

```text
Root CA certificate   (self-signed; stored in your operating system / browser trust store)
   └─ signs ─► Intermediate CA certificate   (sent by the server, or fetched)
                  └─ signs ─► Leaf (server) certificate   for orders.example.com
```

The client validates, in order:

1. **Chain.** The leaf was signed by an intermediate; the intermediate by a root the client already trusts. Each signature verifies, and each certificate's CA flag and key usage permit what it is doing.
2. **Name.** The hostname the client *intended* to reach appears in the leaf's **Subject Alternative Name** (SAN) list, including wildcard rules (`*.example.com` matches `orders.example.com`, not `a.b.example.com`). The old Common Name field is ignored by modern clients.
3. **Validity.** *Now*, according to the **client's clock**, is between `notBefore` and `notAfter`.
4. **Purpose and algorithm.** The certificate is permitted for server authentication; the key and signature algorithms are acceptable.

The server must send the leaf **plus the intermediates**; roots are already in the client. A server that sends only the leaf works in some clients (which fetch missing intermediates themselves) and fails in others (`curl`, many programming runtimes): the classic "works in my browser, fails in my script".

**Handshake outline (TLS 1.3):**

```text
Client → ClientHello  (versions, ciphers, key share, SNI = orders.example.com, ALPN = h2,http/1.1)
Server → ServerHello  (chosen cipher, key share), then encrypted: certificate chain, signature, Finished
Client → verifies chain, name and validity; sends Finished
Both   → application data encrypted with keys derived from the shared secret
```

**SNI** (server name indication) is the hostname the client announces, letting one IP address serve many certificates; **ALPN** negotiates HTTP/2 or HTTP/1.1.

Inspect with:

```bash
openssl s_client -connect orders.example.com:443 -servername orders.example.com -showcerts </dev/null
openssl s_client -connect orders.example.com:443 -servername orders.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
curl -v https://orders.example.com/ 2>&1 | grep -E 'subject|issuer|expire|SSL|TLS'
```

Read `Verify return code:` at the end of `s_client` output: `0 (ok)` or a specific reason such as `20 (unable to get local issuer certificate)`, which means the chain could not be completed (a missing intermediate, or a private CA the client was never given).

### A TLS lab you can run offline

Build a private CA, issue a server certificate, serve it and break it in controlled ways.

```bash
mkdir tlslab && cd tlslab
# 1. A short-lived CA
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout ca.key -out ca.crt -days 7 -subj "/CN=Lab Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"
# 2. A server key and request, then sign with the CA, adding a SAN
openssl req -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout app.key -out app.csr -subj "/CN=app.internal.test"
printf 'subjectAltName=DNS:app.internal.test\nextendedKeyUsage=serverAuth\n' > app.ext
openssl x509 -req -in app.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out app.crt -days 3 -extfile app.ext
# 3. Serve it on a local port
openssl s_server -accept 8443 -cert app.crt -key app.key -www &
# 4. A correct call: map the name to loopback and give curl the CA
curl --resolve app.internal.test:8443:127.0.0.1 --cacert ca.crt https://app.internal.test:8443/ -o /dev/null -sv 2>&1 | grep -E 'SSL|subject|issuer'
```

The `--resolve` flag lets you test a name with no DNS entry; the `--cacert` flag adds your lab CA as the trust anchor for this call only. Now break it, one drill at a time — **never use `curl -k`** when your goal is to observe a verification failure, because it skips exactly the check you are studying.

| Drill | How | What you should observe |
| --- | --- | --- |
| Protocol mismatch | `curl https://127.0.0.1:80` against a plain-HTTP port | A protocol or handshake error; no certificate is ever seen |
| Name mismatch | `curl --resolve other.internal.test:8443:127.0.0.1 --cacert ca.crt https://other.internal.test:8443/` | Hostname verification failure (the SAN lists `app.internal.test` only) |
| Untrusted CA | Same correct call without `--cacert` | Certificate verify failure: `unable to get local issuer certificate` |
| Expired | Run the correct call under a clock set past `notAfter` (for example `faketime '+10 days' curl ...`) | `certificate has expired`; shows validity is checked against the *client's* clock |
| Wrong key usage or missing SAN | Issue a certificate with only a CN and no SAN | Modern clients reject it despite the CN matching |
| Missing intermediate | Add an intermediate CA and serve only the leaf | Clients with only the root fail with a local-issuer error |

Record the exact error line for each; clock skew on *either* side produces expiry or "not yet valid" errors.

## Load balancers

A **load balancer** distributes connections or requests across several backends, checks their health and presents one stable address.

| Type | Works at | Can do | Cannot do |
| --- | --- | --- | --- |
| Layer 4 (network) | TCP/UDP connections | Very fast forwarding; preserve client address; TLS pass-through | Route by URL path or `Host` header |
| Layer 7 (application) | HTTP requests | Route by host and path; terminate TLS; rewrite headers; return custom errors; HTTP/2 to clients | Handle arbitrary non-HTTP protocols |

Behaviours worth knowing:

- **Health checks** remove failing backends. A check that only tests the TCP port keeps a broken-but-listening process in rotation; a check hitting `/ready` removes it. Choose deliberately: too shallow serves errors, too deep (a check that queries the database) can eject *every* backend when the database slows and cause an outage of its own.
- **The client's address** reaches a layer-7 backend in the `X-Forwarded-For` header (or via the PROXY protocol), not as the packet's source. Log it, but trust it only from your own proxy.
- **Idle timeouts** differ at each hop. If the load balancer's idle timeout (often 60 s) is shorter than the backend's keep-alive, it works; if the backend closes a connection that the load balancer thinks is open, the next request fails with `502`. Set backend keep-alive *longer* than the balancer's.
- **`502` versus `504`.** `502 Bad Gateway`: the balancer got an invalid reply or a reset from the backend. `504 Gateway Timeout`: the backend did not answer in time. The code tells you whether the backend was *wrong* or *silent*.

## Diagnosing with `dig` and connection tests

Combine the pieces into a repeatable routine. For each step, predict the result *then* run it.

```bash
# 1. Name: what does each layer say?
getent hosts orders.example.com               # what programs see
dig orders.example.com A +noall +answer       # the configured resolver
dig @8.8.8.8 orders.example.com A +noall +answer  # a public resolver
dig orders.example.com A +noall +comments | grep -E 'status|flags'

# 2. Route:
ip route get 203.0.113.10

# 3. Port, with a timeout so you do not wait for ever:
nc -vz -w 3 203.0.113.10 443

# 4. TLS and identity, against the address but with the right name:
openssl s_client -connect 203.0.113.10:443 -servername orders.example.com -brief </dev/null

# 5. HTTP, with timing:
curl -s -o /dev/null -w 'dns=%{time_namelookup} conn=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} code=%{http_code}\n' \
  https://orders.example.com/health
```

Reading combinations:

| Observation | Interpretation | Next |
| --- | --- | --- |
| `getent` empty, `dig @8.8.8.8` has an answer | Local resolver or search path problem | `resolvectl status`, `/etc/resolv.conf`, VPN or split DNS |
| `dig` fine, `nc` refused immediately | Name is right; nothing listens at that IP:port | `ss -ltnp` on the target; is the IP the right one? |
| `dig` fine, `nc` times out | Route, security group, ACL or firewall | Route tables, rules, test from another source |
| `nc` succeeds, TLS error | The listener is there; identity or chain wrong | Name, SAN, chain, dates, clock |
| TLS fine, `502` | Balancer reached, backend bad | Backend health, `/ready`, balancer target status |
| Works by IP, fails by name | DNS or SNI/Host mismatch | `--resolve`, `-servername`, record, TTL |

## What can go wrong

- **Overlapping CIDRs:** routes exist but traffic goes to the wrong place or nowhere.
- **Subnet exhaustion:** autoscaling fails to launch instances with address errors.
- **Missing return route or stateless ACL without a return rule:** `SYN` leaves, nothing returns; capture at both ends.
- **Stale DNS:** the authoritative query is right, the recursive one wrong.
- **Leaf-only certificate chain:** browser works, script fails with a local-issuer error.
- **Backend closes idle connections early:** sporadic `502` after idle periods.

## Knowledge consolidation

- **CIDR** is arithmetic: block size is a power of two, aligned to itself; find the interesting octet, compute `256 − mask`, round down.
- **Longest prefix wins.** Routing problems are almost always a missing, overlapping or asymmetric route; check the return path too.
- **NAT** rewrites addresses and remembers mappings; inbound needs an explicit mapping, and the far side sees the gateway.
- **DNS** has many caches; query the authoritative server to learn what the zone says and a recursive one to learn what clients see. Negative answers are cached. Lower TTLs *before* changes.
- **Filters stack**: security group, ACL, host firewall, container policy, application. Stateless filters need return rules. A `drop` yields a timeout; a `reject` yields a refusal.
- **TLS** validates chain, name (SAN), dates (client clock) and purpose; servers must send intermediates. Never use `-k` to study a certificate failure.
- **Load balancers** add health checks, timeouts and their own errors; `502` means wrong, `504` means silent.
- **Predict, then run**: write the expected result before each command.

## Exercises

**Exercise 1 — CIDR drill.** For each of `10.20.130.9/19`, `192.168.77.200/26`, `172.31.0.0/20` and `10.0.0.0/28`, give the network address, last address and number of addresses. Then say whether `10.20.159.255` is in the first block.

**Exercise 2 — Plan a network.** From `10.70.0.0/16`, allocate three private `/20` subnets and two public `/24` subnets across three zones, without overlap. Reserve `10.70.128.0/17` for future use. Write the table and check every pair for overlap.

**Exercise 3 — Longest prefix.** Given the routing table in the Routing section, predict the route for `10.60.8.20`, `10.60.9.20`, `10.50.15.1`, `10.50.16.1` and `198.51.100.9`. Verify with `ip route get` on a lab machine after adding equivalent routes (use `ip route add ... dev lo` or a network namespace).

**Exercise 4 — DNS caches.** Create a record in a zone you control with TTL 300. Query it through a recursive resolver, then change the value. Observe, for ten minutes, the authoritative and recursive answers side by side and record when each changed. Repeat with a TTL of 30 and with a deliberately mistaken lookup first (a negative answer).

**Exercise 5 — TLS lab.** Run the TLS lab, trigger each drill and fill a table of exact error text against the failing check (chain, name, validity, purpose).

**Exercise 6 — Filters.** On a snapshot-able VM, create a drop rule and then a reject rule for one port; record each client symptom.

**Exercise 7 — Diagnose.** Have a partner break one of: the DNS record, the route, the bind address, the security-group rule, the certificate SAN. Using the Diagnosing routine, name the cause and quote the evidence line.

**Solution notes.**

*Exercise 1.* `10.20.130.9/19`: block size 32 in the third octet; 130 → 128; network `10.20.128.0`, last `10.20.159.255`, 8,192 addresses; so `10.20.159.255` *is* inside. `192.168.77.200/26`: block 64; 200 → 192; network `192.168.77.192`, last `192.168.77.255`, 64 addresses. `172.31.0.0/20`: block 16; network `172.31.0.0`, last `172.31.15.255`, 4,096. `10.0.0.0/28`: 16 addresses, `10.0.0.0`–`10.0.0.15`.

*Exercise 2.* One valid answer uses `10.70.0.0/20`, `10.70.16.0/20`, `10.70.32.0/20` and public `10.70.240.0/24`, `10.70.241.0/24`, leaving `10.70.128.0/17` untouched. Marks go for the overlap check being explicit and for leaving growth room.

*Exercise 3.* `10.60.8.20` → `10.60.8.0/24` via `tun0`; `10.60.9.20` → `10.60.0.0/16` via `10.50.0.254`; `10.50.15.1` → connected `10.50.0.0/20`; `10.50.16.1` → default (it is *outside* `/20`); `198.51.100.9` → default.

*Exercise 4.* The authoritative answer changes immediately; the recursive answer changes when the cached TTL expires, so expect a delay up to the old TTL (300 s) and a shorter one with TTL 30. A negative answer persists for the SOA negative-caching time, so the record you just created may still appear missing.

*Exercise 5.* Expected errors include `unable to get local issuer certificate`, a hostname mismatch naming the host and SAN list, `certificate has expired`, and a wrong-version or protocol error for the plain port. Exact words differ by tool and version; record the ones you saw.

*Exercise 6.* Drop gives a timeout; reject-with-reset gives immediate refusal. Cloud security groups only allow, so a blocked port appears as a timeout.

*Exercise 7.* Look for evidence that separates causes: `NXDOMAIN` or the wrong address, `Network is unreachable`, the `ss` bind address, a timeout with a correct route, SAN mismatch text.

## Mentoring prompts

Explain why lowering a TTL when you make a change does not shorten the wait. Why can one certificate work in a browser and fail in `curl`? What would you check first when a stateless ACL is suspected, and why?

---

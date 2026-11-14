# T-CLD-02-I — Intermediate Practice

*Chapter: [T-CLD-02 — Networking, DNS and TLS](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-02-i"></a>
#### T-CLD-02-I — Intermediate Practice

**DNS in depth.** Names resolve through a chain: application, local resolver, recursive resolver, authoritative servers. Records you must know:

| Record | Purpose |
| --- | --- |
| A / AAAA | Name to IPv4 / IPv6 address |
| CNAME | Alias to another name |
| MX | Mail routing |
| TXT | Arbitrary text (verification, SPF) |
| NS | Delegation to name servers |

```bash
dig example.com A +noall +answer
dig example.com NS +short
dig @8.8.8.8 example.com            # ask a specific resolver
dig +trace example.com              # follow delegation from the root
```

TTLs control caching; lowering the TTL *before* a planned change shortens the window where clients see old answers. Host DNS is not container DNS: a name like `db` may resolve inside a user-defined container network but not on the host.

**Routing decisions.** `ip route get ADDR` reveals the interface and gateway the kernel would use. For `127.0.0.1`, the loopback interface; for a LAN address, the connected route; for a public address, the default gateway. If `ip route get` fails, fix connectivity before blaming the application.

**Ports and listeners.** A service bound to `127.0.0.1:8000` answers only locally; bound to `0.0.0.0:8000` it answers on all interfaces. A frequent "firewall" problem is actually a loopback-only bind. Check with `ss -ltn`.

**Firewalls.** Host firewalls (`nftables`, `iptables`) and cloud security groups both filter by address, port and protocol. Test one change at a time on a disposable machine you can snapshot:

```bash
sudo nft add table inet lab
sudo nft add chain inet lab input '{ type filter hook input priority 0; }'
sudo nft add rule inet lab input tcp dport 18080 drop
curl -m 3 http://<host>:18080/      # expect a timeout, not "refused"
sudo nft delete table inet lab      # recover
```

Container-published ports are often translated into a bridge network and evaluated in forwarding chains, so a simple input-chain drop may not block them. Use cloud security groups, the container platform's rules or network policies for those.

**TLS essentials.** TLS provides encryption, server authentication via certificates and integrity. The client checks: the certificate chains to a trusted certificate authority (CA), the name matches (the Subject Alternative Name list), the certificate is within its validity dates, and the protocol and cipher are acceptable.

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
curl -v https://example.com 2>&1 | head -30
```

**Reproduce TLS failures without disabling verification.** Never use `curl -k` when your goal is to observe a verification failure; it skips exactly the check you are studying.

| Drill | How | What you should observe |
| --- | --- | --- |
| Protocol mismatch | `curl https://host:80` against a plain-HTTP port | A protocol or handshake error |
| Name mismatch | Serve a certificate for `app.internal.test`, call it as `localhost` with the CA supplied | A hostname verification failure |
| Untrusted CA | Call a self-signed server without supplying its CA | A certificate verify failure |
| Expired certificate | Use a test certificate with past dates | An expiry error |

Record the exact error line for each — they are the vocabulary you will use on-call.

**Exercise.** Create a short-lived self-signed certificate with `openssl`, serve a local page with it and trigger each failure above. Fill a table of error text against failing hop.

# Chapter 1 — Linux, Networking and Cloud Fundamentals (C01)

*Cloud Engineering textbook · Chapter 1 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [C01 course detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) (about 32–40 hours). |
| **Prerequisites** | Terminal comfort; Harbour from [D03](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md) (Compose stack or equivalent). |

## How to study this chapter

Cloud failures are often **path failures**: DNS, route, port, TLS, process, or dependency — mislabeled as “the app is broken.” This chapter builds the operator literacy to prove where the path dies.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer a **disposable** Linux environment (VM, spare cloud micro instance, or documented WSL2 caveats). Do not practise destructive firewall drills on a machine you cannot recover.

This text teaches [C01 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md). Checklist bar: *given a connectivity failure, diagnose and restore reachability using only your network/path notes and runbook.*

> **Safety:** Prefer throwaway VMs. Snapshot before firewall experiments. No production credentials. If using a cloud VM, attach a budget alarm first (C02 deepens billing).

### Learning outcomes

1. Debug Linux services with process, socket and log evidence.  
2. Trace client → DNS → route → port → TLS → process.  
3. Explain shared responsibility and IaaS/PaaS placement for Harbour.  
4. Maintain a Harbour connectivity runbook another engineer can follow.  
5. Restore a planted outage without reboot-as-ritual.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
uname -a
command -v ss curl dig ip || echo "Install iproute2 / curl / dnsutils as needed"
mkdir -p docs/runbooks docs/decisions
# Harbour should start (D03 Compose or your documented path):
# docker compose up -d   # example — use YOUR stack instructions
```

---

## Section 1.1 — Linux operator essentials

### 1.1.1 Who am I, what can I break?

```bash
id
whoami
sudo -l 2>/dev/null || echo "no sudo — note the limitation"
```

**Reflect:** What is the blast radius of your user vs `root`?

### 1.1.2 Worked example — find Harbour’s process and sockets

With Harbour listening (Compose publishes API to host `8000` in D03/D07 labs):

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
# Process / socket view (names vary if inside Compose network only):
ss -ltnp | grep -E ':8000|:5432' || true
docker compose ps 2>/dev/null || true
```

If the API runs **only** in Compose without host publish, exec into the container:

```bash
docker compose exec api sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
docker compose exec api sh -c 'ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null || true'
```

**Expected:** You can name the process that accepts HTTP and the address:port it binds.

### 1.1.3 Worked example — logs beat vibes

```bash
docker compose logs api --tail=50 2>/dev/null
# On a systemd-hosted service (if you wrapped Harbour that way):
# journalctl -u harbour-api -n 50 --no-pager
```

Correlate one failed `curl` with one log line (timestamp).

### 1.1.4 Users, permissions and “permission denied”

```bash
ls -la app/harbour_api/main.py 2>/dev/null || ls -la
# Demonstrate reading a file as your user; note what would break if the service user differed
```

**Practice — reproduce:** Stop the API container/process; show `curl` failure **and** `ss` without the listener; start it; show recovery.

**Verify:** You can explain PID ↔ port ↔ log without opening a GUI.

---

## Section 1.2 — The reachability path

### 1.2.1 Mental model

```text
Client
  → DNS name (optional)
  → IP route / local stack
  → TCP port (firewall / security group / published port)
  → TLS (optional)
  → Process accept()
  → App logic (/health vs /ready)
  → Dependency (e.g. Postgres on internal network)
```

Each hop can fail **independently**. Record which hop you are testing.

### 1.2.2 Worked example — DNS

```bash
getent hosts localhost
dig +short example.com @1.1.1.1 || nslookup example.com
# For a local Compose service name from the HOST, DNS often does NOT resolve "db" —
# that name exists on the Compose network only (D03 lesson). Prove it:
getent hosts db || echo "expected: db not in host DNS"
```

**Expected:** You never assume host DNS equals container DNS.

### 1.2.3 Worked example — routes and interfaces

```bash
ip -br a
ip route
ping -c 1 127.0.0.1
```

### 1.2.4 Worked example — ports and connectivity

```bash
# TCP check without HTTP semantics:
curl -v --connect-timeout 2 http://127.0.0.1:8000/health || true
# From another machine/VM (if any), replace 127.0.0.1 with the lab IP and note firewall behaviour
```

### 1.2.5 Worked example — `/health` vs `/ready` (D03 contract)

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS -o /tmp/ready.json -w "%{http_code}\n" http://127.0.0.1:8000/ready
cat /tmp/ready.json
```

| Endpoint | Means |
| --- | --- |
| `/health` | Process up |
| `/ready` | Dependencies OK (or `unconfigured` if no `DATABASE_HOST`) |

**Practice — reproduce:** `docker compose stop db` (if present); compare `/health` vs `/ready`.

**Verify:** You can say which hop failed when `/ready` is 503 but `/health` is 200.

---

## Section 1.3 — TLS and trust (operator view)

### 1.3.1 Concept

TLS failure modes: wrong clock, missing CA, name mismatch (SNI/CN), expired cert, HTTP spoken to HTTPS port.

### 1.3.2 Worked example — inspect without claiming production PKI

```bash
# Against a public site (training):
curl -vI https://example.com 2>&1 | head -n 40
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
```

For local Harbour HTTP (no TLS yet): document that **TCP+HTTP success ≠ internet exposure ready**. TLS termination may sit on a reverse proxy or cloud load balancer in C02–C03.

**Verify:** One paragraph in the runbook: where TLS will terminate for Harbour later.

---

## Section 1.4 — Cloud vocabulary that unblocks C02

### 1.4.1 Shared responsibility

| Layer | Typical owner |
| --- | --- |
| Physical DC, hypervisor | Cloud provider |
| Guest OS patching (IaaS VM) | You |
| Managed DB engine patches | Provider; **your** schema/auth still you |
| Application code, IAM policies you write | You |

### 1.4.2 Regions, AZs, blast radius

One AZ outage vs region event — what Harbour topology survives (honest: single-node Compose survives neither meaningfully).

### 1.4.3 IaaS / PaaS placement for Harbour

| Component | Local DevOps lab | Likely AWS shape (C02–C03) |
| --- | --- | --- |
| API | Container on Docker/kind | ECS/Fargate or EKS later |
| DB | Compose Postgres (unpublished port) | RDS or still container (justify) |
| Edge | localhost publish | ALB / API Gateway |

**ADR stub** (`docs/decisions/0101-harbour-placement.md`): what you run as IaaS vs managed in the next modules.

**Verify:** You can explain why D05’s training public-subnet tasks are a cost trade-off, not a blueprint.

---

## Section 1.5 — Plant failures and diagnose (working sequence)

Use **one** failure at a time. Write symptoms before fixing.

### 1.5.1 Worked example — process down

```bash
docker compose stop api 2>/dev/null || true
curl -sS -o /dev/null -w "%{http_code}\n" --connect-timeout 2 http://127.0.0.1:8000/health || echo "CONNECT_FAIL"
ss -ltn | grep 8000 || echo "no listener"
# Diagnose: hop = process/port
docker compose start api 2>/dev/null || docker compose up -d api
curl -sS http://127.0.0.1:8000/health
```

### 1.5.2 Worked example — dependency down

```bash
docker compose stop db 2>/dev/null || true
curl -sS -w "\n%{http_code}\n" http://127.0.0.1:8000/health
curl -sS -w "\n%{http_code}\n" http://127.0.0.1:8000/ready
docker compose start db
# wait for healthy, then:
curl -sS http://127.0.0.1:8000/ready
```

### 1.5.3 Worked example — wrong publish / firewall simulation

If you can change Compose ports temporarily: map API to `127.0.0.1:8000` only and try from another interface; **or** use `iptables`/`nft` on a disposable VM to DROP port 8000 (snapshot first).

Record: client error type (timeout vs refused vs HTTP 5xx).

### 1.5.4 Challenge — blind restart ban

Restore a failure **without** `docker compose restart` as the first command. Restarts are allowed only after the hop is identified.

---

## Section 1.6 — Harbour connectivity runbook

### 1.6.1 Worked example — write the runbook

Create `docs/runbooks/harbour-connectivity.md`:

```markdown
# Harbour connectivity runbook

## Path diagram
(client) → … → (api) → (db)
_Update boxes to match YOUR lab._

## Healthy checks (ordered)
1. DNS / name resolution: …
2. Route / ping or ip route: …
3. TCP port: `ss` / `curl --connect-timeout`
4. HTTP /health → expect 200
5. HTTP /ready → expect 200 (or documented unconfigured)
6. Dependency: db healthy / SELECT 1

## Failure matrix
| Symptom | Likely hop | Next command |
| --- | --- | --- |
| Connection refused | Process/port | ss -ltn; compose ps |
| Timeout | Firewall/route | ip route; SG/firewall |
| 503 on /ready only | Dependency | db logs; DATABASE_* |
| TLS error | Cert/trust | openssl s_client |

## Recovery
- Revert config changes; prefer compose up of the failed service
- Do not delete volumes unless data loss is accepted

## Stop / escalate
- Suspected account compromise; disk full on shared host; …
```

### 1.6.2 Practice — reproduce

Hand the runbook to a peer (or yourself next day). Plant a failure; they must restore using only the runbook.

**Verify:** Checklist C01 evidence folder links diagram, command list, recovery record.

---

## Practical Assessment — Chapter 1 — restore reachability

Align with [C01 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) and Final Project Checklist C01.

### Required deliverables

1. Reachability diagram for your actual topology.  
2. Diagnostic command list with sample healthy output.  
3. Planted failure + diagnosis (named hop) + recovery record.  
4. Runbook committed under `docs/runbooks/`.  
5. Shared-responsibility note (local vs future AWS edge).

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Linux | Restarts blindly | PID/socket/log evidence | systemd unit or equivalent owned |
| Network | Port scan folklore | Ordered hop tests | TLS hop documented |
| Cloud concepts | Buzzwords | Shared responsibility mapped | Honest D05 trade-off critique |
| Runbook | Notes for self | Peer can restore from it | Failure matrix covers ≥3 hops |

**Completion:** **Competent** on every row.

### Example conclusion (evidence still required)

> Compose Harbour on laptop: client→`:8000`→api→`db` DNS on bridge network. Planted `stop db`: `/health` 200, `/ready` 503; restored db; runbook updated. Peer restored a stopped api using only the runbook.

---

## Quick reference

| Symptom | First check |
| --- | --- |
| Connection refused | Listener/`compose ps` |
| Timeout | Route/firewall/SG |
| HTTP 5xx | App logs |
| Ready 503 / health 200 | Dependency |
| Works on host, not by name `db` | Wrong network namespace |

## Glossary

| Term | Meaning |
| --- | --- |
| Bind address | Interface IP the process listens on |
| Published port | Host port mapped into a container |
| Hop | One stage of the reachability path |
| Shared responsibility | Split of security duties with the provider |

## References

- `ss(8)`, `ip(8)`, `curl(1)`  
- [AWS shared responsibility](https://aws.amazon.com/compliance/shared-responsibility-model/)  
- [D03 Docker](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md) · [Cloud overview](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/CLOUD%20Overview.md)

**Course detail:** [C01](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) · **Next chapter:** Chapter 2 — AWS Cloud Foundations (not yet authored) · **Checklist:** [Final Project Checklist · C01](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)

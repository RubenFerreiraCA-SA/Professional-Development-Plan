# Chapter 1 — Linux, Networking and Cloud Fundamentals (C01)

*Cloud Engineering textbook · Chapter 1 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [C01 course detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) (about 32–40 hours). |
| **Prerequisites** | Terminal comfort; Harbour from [D03](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md) with `app/docker-compose.yml`. |

## How to study this chapter

Cloud failures are often **path failures**: DNS, route, port, TLS, process, or dependency — mislabeled as “the app is broken.” This chapter builds the operator literacy to prove where the path dies, using **ordered hop tests** and written evidence.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer a **disposable** Linux environment for firewall drills (VM snapshot, spare cloud micro instance). Do not practise destructive `nft`/`iptables` rules on a machine you cannot recover. WSL2 is fine for Compose/process labs; note where firewall behaviour differs from a real VM.

This text teaches [C01 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md). Checklist bar: *given a connectivity failure, diagnose and restore reachability using only your network/path notes and runbook.*

> **Safety:** Snapshot before firewall experiments. No production credentials. If using a cloud VM, attach a budget alarm first (C02 deepens billing).

### Learning outcomes

1. Debug Linux services with process, permission, socket and log evidence.  
2. Trace client → DNS → route → port → TLS → process → dependency.  
3. Distinguish **application** failure from **network** failure using command output.  
4. Explain shared responsibility and IaaS/PaaS placement for Harbour.  
5. Maintain a Harbour connectivity runbook another engineer can follow.

### Before you begin — Compose path (mandatory)

D03 places Compose at **`app/docker-compose.yml`**. All Compose commands in this chapter use an explicit file path so they work from the repo root.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export HARBOUR_COMPOSE="${HARBOUR_COMPOSE:-$HARBOUR_ROOT/app/docker-compose.yml}"
cd "$HARBOUR_ROOT"

test -f "$HARBOUR_COMPOSE" || {
  echo "Missing $HARBOUR_COMPOSE — complete D03 Compose first"
  exit 1
}

uname -a
command -v ss curl dig ip || echo "Install iproute2 / curl / dnsutils as needed"

mkdir -p docs/runbooks docs/decisions

# Start Harbour from the correct Compose file:
docker compose -f "$HARBOUR_COMPOSE" up -d
docker compose -f "$HARBOUR_COMPOSE" ps
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
```

**Alias (optional, session-local):**

```bash
alias hc='docker compose -f "$HARBOUR_COMPOSE"'
# then: hc ps | hc logs api | hc stop db
```

Do **not** run bare `docker compose …` from `$HARBOUR_ROOT` without `-f` — Compose will not find `app/docker-compose.yml` by default.

---

## Section 1.1 — Linux operator essentials

### 1.1.1 Who am I, what can I break?

```bash
id
whoami
sudo -l 2>/dev/null || echo "no sudo — note the limitation for later firewall drills"
```

**Reflect:** What is the blast radius of your user vs `root`?

### 1.1.2 Worked example — users, groups and permission denied

```bash
# Ownership of Harbour sources (paths from D03):
ls -la "$HARBOUR_ROOT/app/harbour_api/main.py"
stat -c '%U:%G %a %n' "$HARBOUR_ROOT/app/harbour_api/main.py" 2>/dev/null \
  || stat -f '%Su:%Sg %Mp%Lp %N' "$HARBOUR_ROOT/app/harbour_api/main.py"

# Create a throwaway unreadable file and prove the failure mode:
umask 077
echo secret > /tmp/harbour-perm-demo
chmod 600 /tmp/harbour-perm-demo
# As your user:
cat /tmp/harbour-perm-demo
# Simulate another user (if you have sudo):
sudo -u nobody cat /tmp/harbour-perm-demo 2>&1 | head -n 5 || true
rm -f /tmp/harbour-perm-demo
```

**Expected:** You can explain mode bits (owner/group/other) and why a service user different from your login user would get `Permission denied` on a `600` secret file. Record: never chmod `777` to “make Harbour work.”

### 1.1.3 Worked example — find Harbour’s process and sockets

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
ss -ltnp | grep -E ':8000|:5432' || true
docker compose -f "$HARBOUR_COMPOSE" ps

# Inside the API container (slim images often lack ps — use /proc):
docker compose -f "$HARBOUR_COMPOSE" exec api \
  sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
docker compose -f "$HARBOUR_COMPOSE" exec api \
  sh -c 'ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null || true'
```

**Expected:** Host shows a listener on `:8000` (published port). Container PID 1 cmdline is the app server. Postgres is **not** published to the host in D03 — `:5432` on the host may be absent; that is correct.

### 1.1.4 Worked example — logs beat vibes

```bash
docker compose -f "$HARBOUR_COMPOSE" logs api --tail=50
# Force an error and correlate timestamps:
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/no-such-route || true
docker compose -f "$HARBOUR_COMPOSE" logs api --tail=20
```

On a systemd-hosted unit (optional Advanced): `journalctl -u harbour-api -n 50 --no-pager`.

### 1.1.5 Worked example — disk and memory pressure symptoms

```bash
df -h /
free -h 2>/dev/null || vm_stat 2>/dev/null | head
docker compose -f "$HARBOUR_COMPOSE" stats --no-stream
```

**Practice — reproduce:** Stop the API; show `curl` failure **and** `ss` without `:8000`; start it; show recovery — all with `-f "$HARBOUR_COMPOSE"`.

**Verify:** You can explain PID ↔ port ↔ log ↔ permission without a GUI.

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
  → Dependency (Postgres on Compose network only)
```

Each hop can fail **independently**. Label which hop you are testing in every note.

### 1.2.2 Worked example — DNS (host vs Compose network)

```bash
getent hosts localhost
dig +short example.com @1.1.1.1 || nslookup example.com

# Compose service name "db" is NOT in host DNS:
getent hosts db || echo "expected: db not resolvable on host"

# From inside the API container, db SHOULD resolve:
docker compose -f "$HARBOUR_COMPOSE" exec api \
  sh -c 'getent hosts db || python -c "import socket; print(socket.getaddrinfo(\"db\", 5432)[0][4])"'
```

**Expected:** Host cannot use hostname `db`; the API container can. Never assume host DNS equals container DNS.

### 1.2.3 Worked example — interfaces, routes and decisions

```bash
ip -br a
ip route
ip route get 1.1.1.1
ip route get 127.0.0.1
ping -c 1 127.0.0.1
```

| Command | What it tells you |
| --- | --- |
| `ip -br a` | Which interfaces are up and their addresses |
| `ip route` | Default gateway and connected prefixes |
| `ip route get ADDR` | Which path the kernel would use for ADDR |

**Decision drill:** For destination `127.0.0.1` vs your LAN IP vs a public IP, write one sentence each on which interface/route wins. If `ip route get` fails, fix connectivity before blaming Harbour.

### 1.2.4 Worked example — ports and TCP vs HTTP

```bash
# TCP/HTTP to published API:
curl -v --connect-timeout 2 http://127.0.0.1:8000/health
# Connection refused vs timeout — write down which you see when API is stopped vs firewalled later
docker compose -f "$HARBOUR_COMPOSE" stop api
curl -v --connect-timeout 2 http://127.0.0.1:8000/health 2>&1 | tail -n 15
docker compose -f "$HARBOUR_COMPOSE" start api
# wait until healthy:
until curl -sf http://127.0.0.1:8000/health >/dev/null; do sleep 1; done
```

**Expected:** Stopped process → typically **connection refused** (nothing listening). Contrast with §1.5 firewall DROP → often **timeout**. That distinction is assessment gold.

### 1.2.5 Worked example — `/health` vs `/ready` (D03 contract)

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS -o /tmp/ready.json -w "%{http_code}\n" http://127.0.0.1:8000/ready
cat /tmp/ready.json

docker compose -f "$HARBOUR_COMPOSE" stop db
curl -sS -w " health:%{http_code}\n" -o /dev/null http://127.0.0.1:8000/health
curl -sS -w " ready:%{http_code}\n" http://127.0.0.1:8000/ready; echo
docker compose -f "$HARBOUR_COMPOSE" start db
until curl -sf http://127.0.0.1:8000/ready >/dev/null; do sleep 1; done
```

| Endpoint | Means |
| --- | --- |
| `/health` | Process up |
| `/ready` | Dependencies OK (or `unconfigured` if no `DATABASE_HOST`) |

**Verify:** You can name the hop when `/ready` is 503 but `/health` is 200 (**dependency**, not network-to-API).

---

## Section 1.3 — TLS and trust (operator view)

### 1.3.1 Concept

TLS failure modes you must recognise from output: clock skew, missing CA, name mismatch (SNI/CN), expired cert, plain HTTP to an HTTPS port.

Local Harbour in D03 is often **HTTP on localhost**. Document where TLS will terminate later (C02/C03 load balancer or reverse proxy). Still practise TLS diagnosis against a public endpoint so the failure vocabulary is real.

### 1.3.2 Worked example — healthy TLS baseline

```bash
curl -vI --connect-timeout 5 https://example.com 2>&1 | head -n 45
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer
```

### 1.3.3 Worked example — TLS failures you can reproduce

Do **not** use `curl -k` / `--insecure` when the goal is to observe verification failure — that flag skips the check you are trying to learn.

**A — HTTP spoken to HTTPS port (protocol mismatch):**

```bash
curl -v --connect-timeout 5 http://example.com:443/ 2>&1 | tail -n 20
# Often: empty reply / SSL errors — note the symptom class
```

**B — Hostname mismatch (controlled local certificate — deterministic):**

Create a short-lived self-signed cert whose **CN/SAN is `harbour-tls.local`**, serve HTTPS with it, then call the server as `localhost` so the name does not match. Verification must stay **on** (no `-k`).

```bash
mkdir -p /tmp/harbour-tls-c01 && cd /tmp/harbour-tls-c01
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -keyout key.pem -out cert.pem \
  -subj "/CN=harbour-tls.local" \
  -addext "subjectAltName=DNS:harbour-tls.local"

# Terminal 1 — TLS listener on 8443 (-www serves a simple HTTP response so curl does not hang):
openssl s_server -www -accept 8443 -cert cert.pem -key key.pem >/tmp/harbour-tls-s_server.log 2>&1 &
echo $! > /tmp/harbour-tls-s_server.pid
sleep 1

# Terminal 2 — trust this cert as a CA for the test, but use the WRONG hostname:
curl -v --connect-timeout 5 --max-time 10 \
  --cacert /tmp/harbour-tls-c01/cert.pem \
  https://localhost:8443/ 2>&1 | tee /tmp/harbour-tls-mismatch.txt | tail -n 30
# Expected: certificate verify failed / hostname mismatch / "does not match" (wording varies).
# Do NOT add -k. If you add -k, the drill is invalid.

# Optional positive control — same cert, matching name via --resolve:
curl -v --connect-timeout 5 --max-time 10 \
  --cacert /tmp/harbour-tls-c01/cert.pem \
  --resolve harbour-tls.local:8443:127.0.0.1 \
  https://harbour-tls.local:8443/ 2>&1 | tail -n 15
# Expect TLS success and a basic HTTP body from s_server -www.

kill "$(cat /tmp/harbour-tls-s_server.pid)" 2>/dev/null || true
cd "$HARBOUR_ROOT"
```

Record the exact `curl` stderr line that proves **hostname verification** failed (not “untrusted CA” alone — you passed `--cacert`).

**C — Untrusted / expired CA (observe verify error without `-k`):**

```bash
curl -vI --connect-timeout 5 https://expired.badssl.com/ 2>&1 | tee /tmp/harbour-tls-expired.txt | tail -n 30
# Expected: SSL certificate problem / verify failed. Using -k would hide this — do not.
```

**Capture table** (fill with your actual stderr snippets):

| Drill | Symptom keywords | Hop |
| --- | --- | --- |
| A | | TLS/protocol |
| B | | TLS/name (local cert) |
| C | | TLS/trust |

**Verify:** Runbook TLS section lists these three, forbids `-k` for mismatch/trust drills, and notes localhost Harbour may still be HTTP-only.

---

## Section 1.4 — Cloud vocabulary that unblocks C02

### 1.4.1 Shared responsibility

| Layer | Typical owner |
| --- | --- |
| Physical DC, hypervisor | Cloud provider |
| Guest OS patching (IaaS VM) | You |
| Managed DB engine patches | Provider; **your** schema/auth still you |
| Application code, IAM policies you write | You |
| Security group / firewall rules you configure | You |

### 1.4.2 Regions, AZs, blast radius

One AZ outage vs region event — what Harbour topology survives (honest: single-node Compose survives neither meaningfully).

### 1.4.3 IaaS / PaaS placement for Harbour

| Component | Local DevOps lab | Likely AWS shape (C02–C03) |
| --- | --- | --- |
| API | Container via Compose | ECS/Fargate or EKS later |
| DB | Compose Postgres (unpublished host port) | RDS or still container (justify) |
| Edge | localhost publish | ALB / TLS termination |

**ADR stub** (`docs/decisions/0101-harbour-placement.md`): what you run as IaaS vs managed next.

**Verify:** You can explain why D05’s training public-subnet tasks are a cost trade-off, not a blueprint.

---

## Section 1.5 — Application and dependency failures

Use **one** failure at a time. Write symptoms before fixing. Always `-f "$HARBOUR_COMPOSE"`.

### 1.5.1 Worked example — process down (application hop)

```bash
docker compose -f "$HARBOUR_COMPOSE" stop api
curl -sS -o /dev/null -w "%{http_code}\n" --connect-timeout 2 http://127.0.0.1:8000/health || echo "CONNECT_FAIL"
ss -ltn | grep 8000 || echo "no listener"
# Typical: connection refused + no listener → process/port hop
docker compose -f "$HARBOUR_COMPOSE" start api
until curl -sf http://127.0.0.1:8000/health >/dev/null; do sleep 1; done
```

### 1.5.2 Worked example — dependency down (app dependency hop)

```bash
docker compose -f "$HARBOUR_COMPOSE" stop db
curl -sS -w "\nhealth:%{http_code}\n" -o /dev/null http://127.0.0.1:8000/health
curl -sS -w "\nready:%{http_code}\n" http://127.0.0.1:8000/ready; echo
# Typical: health 200, ready 503 → NOT a client→API network failure
docker compose -f "$HARBOUR_COMPOSE" start db
until curl -sf http://127.0.0.1:8000/ready >/dev/null; do sleep 1; done
```

### 1.5.3 Challenge — blind restart ban

Restore a failure **without** `docker compose … restart` as the first command. Restarts are allowed only after the hop is identified.

---

## Section 1.6 — Network failure drill (complete, reproducible)

Application stops (§1.5) are not enough. You need one **network-path** failure with baseline → fault → evidence → recovery.

Pick **Path A** (works on a normal laptop with Compose) **or** **Path B** (disposable Linux VM with `nft`). Do at least one fully; Advanced learners do both.

### 1.6.1 Path A — publish only on loopback (Compose network publish fault)

**Idea:** Bind host publish to `127.0.0.1:8000` so the API works locally but fails from another address/interface — a classic “firewall / wrong bind” class failure without kernel firewall skills.

**1. Baseline**

```bash
docker compose -f "$HARBOUR_COMPOSE" ps
curl -sf http://127.0.0.1:8000/health && echo baseline-ok
ss -ltn | grep 8000
```

**2. Controlled fault** — in `app/docker-compose.yml`, change the API ports mapping from `"8000:8000"` to `"127.0.0.1:8000:8000"` (loopback only). Recreate:

```bash
docker compose -f "$HARBOUR_COMPOSE" up -d --force-recreate api
ss -ltn | grep 8000
# Expect something like 127.0.0.1:8000 listeners, not *:8000 / 0.0.0.0:8000
curl -sf http://127.0.0.1:8000/health && echo still-works-on-loopback
```

From another host on the LAN (or a second VM), `curl http://<laptop-lan-ip>:8000/health` should **fail** (refused/timeout/unreachable). If you have no second machine, document `ss` evidence that the socket is loopback-only and explain why a remote client cannot connect.

**3. Diagnostic evidence (record verbatim)**

```bash
ss -ltn | grep 8000
ip -br a
# Remote client output OR written proof that bind is 127.0.0.1-only
```

**4. Recovery** — restore `"8000:8000"`, recreate, confirm `0.0.0.0:8000` or `*:8000` as before:

```bash
docker compose -f "$HARBOUR_COMPOSE" up -d --force-recreate api
ss -ltn | grep 8000
curl -sf http://127.0.0.1:8000/health
```

### 1.6.2 Path B — firewall DROP against a **native** host listener (INPUT works here)

Docker-published ports are often **DNAT’d into a bridge** and evaluated on **FORWARD** / Docker’s own chains — **not** the host `INPUT` hook. Dropping `tcp dport 8000` on `INPUT` may leave `http://127.0.0.1:8000` working and teach the wrong lesson.

**Competent path:** fire wall a **native** process on a dedicated port so `INPUT` is the correct control plane.

**Only on a disposable VM/host you can snapshot** if you are unsure about firewall recovery.

```bash
# 1) Baseline — native listener on 18080 (not Docker-published Harbour):
python3 -m http.server 18080 --bind 127.0.0.1 >/tmp/harbour-native-http.log 2>&1 &
echo $! > /tmp/harbour-native-http.pid
sleep 1
curl -sf --connect-timeout 2 http://127.0.0.1:18080/ >/dev/null && echo native-baseline-ok
ss -ltn | grep 18080

# 2) Controlled fault — INPUT drop for 18080:
sudo nft add table inet harbour_c01
sudo nft 'add chain inet harbour_c01 input { type filter hook input priority 0; policy accept; }'
sudo nft add rule inet harbour_c01 input tcp dport 18080 drop

# 3) Evidence — often TIMEOUT; listener still present:
curl -v --connect-timeout 3 http://127.0.0.1:18080/ 2>&1 | tee /tmp/harbour-fw-drop.txt | tail -n 20
ss -ltn | grep 18080
# Contrast §1.5.1: process down → refused + no listener; firewall → timeout + listener present

# 4) Recovery:
sudo nft delete table inet harbour_c01
curl -sf --connect-timeout 2 http://127.0.0.1:18080/ >/dev/null && echo native-recovered-ok
kill "$(cat /tmp/harbour-native-http.pid)" 2>/dev/null || true
```

If `nft` is unavailable: `sudo iptables -I INPUT -p tcp --dport 18080 -j DROP` then delete that rule on recovery — still snapshot first.

### 1.6.3 Advanced — why INPUT often fails against Docker-published Harbour

Optional, after Path B succeeds. Keep Harbour published on host `:8000`.

```bash
curl -sf http://127.0.0.1:8000/health && echo docker-publish-ok
sudo nft add table inet harbour_c01_docker
sudo nft 'add chain inet harbour_c01_docker input { type filter hook input priority 0; policy accept; }'
sudo nft add rule inet harbour_c01_docker input tcp dport 8000 drop
curl -v --connect-timeout 3 http://127.0.0.1:8000/health 2>&1 | tail -n 15
# Frequently STILL succeeds — traffic to published ports may never hit this INPUT rule.
sudo nft delete table inet harbour_c01_docker
```

**Record the outcome honestly.** If Harbour stayed reachable, you have evidence that **container publish ≠ a simple INPUT filter**. Production controls then live in security groups, `DOCKER-USER` (iptables), or CNI policies — not a naive host INPUT drop. Do **not** claim a Docker firewall drill passed unless you verified the block on the actual path (e.g. remote client through FORWARD, or a documented `DOCKER-USER` rule that you tested end-to-end).

Assessment credit for “network failure” requires Path A and/or Path B (native). The Docker INPUT experiment is a learning add-on, not a substitute when it fails to block.

### 1.6.4 Compare evidence classes

| Failure | `ss` listener | `curl` symptom | Hop |
| --- | --- | --- | --- |
| `stop api` | Absent | Refused / CONNECT_FAIL | Process |
| `stop db` | Present | health 200, ready 503 | Dependency |
| Loopback-only publish | `127.0.0.1:8000` only | Remote fail / local OK | Publish/bind |
| Native `:18080` + INPUT DROP | Present on 18080 | Timeout | Firewall |
| INPUT DROP on Docker `:8000` | Often present | Often **still OK** | Wrong hook — see §1.6.3 |

**Practice — reproduce:** Without looking at your notes, be handed app vs network evidence and name the hop from output alone.

**Verify:** Progress Log contains paste of `ss` + `curl` for an **application** failure and a **network** failure (Path A or native Path B).

---

## Section 1.7 — Harbour connectivity runbook

### 1.7.1 Worked example — write the runbook

Create `docs/runbooks/harbour-connectivity.md`:

```markdown
# Harbour connectivity runbook

## Compose invocation
export HARBOUR_ROOT=…
export HARBOUR_COMPOSE=$HARBOUR_ROOT/app/docker-compose.yml
docker compose -f "$HARBOUR_COMPOSE" …

## Path diagram
(client) → host:8000 → api container → db:5432 (Compose DNS)
_Update to match YOUR lab._

## Healthy checks (ordered)
1. `docker compose -f "$HARBOUR_COMPOSE" ps`
2. DNS: host vs `exec api getent hosts db`
3. `ip route` / `ip route get`
4. `ss -ltn | grep 8000` — note bind *:8000 vs 127.0.0.1:8000
5. `curl --connect-timeout 2` — refused vs timeout
6. HTTP /health → 200
7. HTTP /ready → 200 (or documented unconfigured)
8. Dependency: db healthy

## Failure matrix
| Symptom | Likely hop | Next command |
| --- | --- | --- |
| Connection refused, no listener | Process | compose ps; logs api |
| Timeout, listener present | Firewall/filter | Prefer native-port INPUT drill; do not assume INPUT blocks Docker publish |
| Works on 127.0.0.1 only | Bind/publish | ss -ltn; compose ports |
| 503 on /ready only | Dependency | compose ps db; ready body |
| TLS verify / name mismatch | TLS | openssl s_client; curl -v |

## Recovery
- Identify hop first; then start service / fix publish / delete firewall table
- Prefer `compose start` / recreate over blind `restart`
- Do not delete volumes unless data loss is accepted

## Stop / escalate
- Suspected compromise; disk full; inability to snapshot before firewall changes
```

### 1.7.2 Practice — peer restore

Hand the runbook to a peer (or yourself next day). Plant **either** an app failure **or** a network failure. They restore using only the runbook and must state which class it was from evidence.

---

## Practical Assessment — Chapter 1 — restore reachability

Align with [C01 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) and Final Project Checklist C01.

### Required deliverables

1. Reachability diagram for your actual topology.  
2. Diagnostic command list using `-f "$HARBOUR_COMPOSE"` with sample healthy output.  
3. **Application** failure record (e.g. stopped api or db) with hop named.  
4. **Network** failure record (Path A and/or B) with `ss`+`curl` evidence showing a different symptom class.  
5. Runbook committed under `docs/runbooks/`.  
6. Shared-responsibility note (local vs future AWS edge/SG).  
7. Short comparison: how you told app failure from network failure using output alone.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Linux | Restarts blindly | PID/socket/log/permission evidence | systemd or equivalent owned |
| Network | Port folklore | Ordered hops + one complete network drill | Path A and Path B |
| App vs net | Cannot distinguish | Refused vs timeout vs ready-503 from evidence | Peer restore both classes |
| TLS | Skipped | Three failure drills recorded | Termination plan for Harbour edge |
| Runbook | Notes for self | Peer can restore from it | Matrix covers app + network hops |
| Cloud concepts | Buzzwords | Shared responsibility mapped | Honest D05 trade-off critique |

**Completion:** **Competent** on every row.

### Example conclusion (evidence still required)

> Compose via `-f $HARBOUR_ROOT/app/docker-compose.yml`. App: `stop api` → refused, no listener. Network: Path B native `:18080` INPUT DROP → timeout with listener present; also noted INPUT on Docker `:8000` did not block (FORWARD/NAT lesson). TLS B: local CN=`harbour-tls.local` vs `https://localhost` without `-k` → hostname verify error. Runbook committed.

---

## Quick reference

| Symptom | First check |
| --- | --- |
| `compose` errors about missing file | `-f "$HARBOUR_COMPOSE"` → `app/docker-compose.yml` |
| Connection refused | Listener / `compose ps` |
| Timeout | Firewall/SG / bind address |
| HTTP 5xx | App logs |
| Ready 503 / health 200 | Dependency |
| Works on host, not by name `db` | Wrong network namespace |

## Glossary

| Term | Meaning |
| --- | --- |
| Bind address | Interface IP the process/publish listens on |
| Published port | Host port mapped into a container |
| Hop | One stage of the reachability path |
| Connection refused | Nothing accepted the TCP handshake (often no listener) |
| Timeout | Packets dropped/filtered or blackholed along the path |

## References

- `ss(8)`, `ip(8)`, `curl(1)`, `nft(8)`  
- [AWS shared responsibility](https://aws.amazon.com/compliance/shared-responsibility-model/)  
- [D03 Docker](../4.1%20DevOps/D03%20Docker%20and%20Containerization.md) · [Cloud overview](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/CLOUD%20Overview.md)

**Course detail:** [C01](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) · **Next chapter:** [Chapter 2 — AWS Cloud Foundations](C02%20AWS%20Cloud%20Foundations.md) · **Checklist:** [Final Project Checklist · C01](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)

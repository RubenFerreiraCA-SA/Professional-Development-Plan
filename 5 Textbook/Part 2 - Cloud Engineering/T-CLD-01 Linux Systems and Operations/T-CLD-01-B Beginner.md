# T-CLD-01-B — Beginner Foundations

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-b"></a>
#### T-CLD-01-B — Beginner Foundations

**Who am I, what can I break?**

```bash
whoami                 # current user
id                     # uid, gid, supplementary groups
sudo -l                # what may I run as root? (if sudo is available)
pwd; ls -la            # where am I and what is here?
```

Your blast radius is whatever your user may change. `root` can change everything, so use it deliberately and briefly.

**Files and permissions.** Every file has an owner, a group and permission bits for owner, group and others:

```bash
ls -l secret.txt
# -rw------- 1 alice alice 20 Mar  1 10:00 secret.txt
chmod 600 secret.txt     # owner read/write only
chmod 640 app.conf       # owner rw, group read, others none
chown app:app app.conf   # change owner and group (needs privilege)
```

Read `-rw-r-----` as: owner read+write, group read, others nothing. A service running as user `app` cannot read a `600` file owned by `alice` — you get `Permission denied`. The fix is to give the right owner or group access, never `chmod 777`.

**Processes.**

```bash
ps aux | head              # snapshot of processes
ps -o pid,ppid,user,cmd -p 1234
top                        # live view (q to quit)
kill 1234                  # polite stop (SIGTERM)
kill -9 1234               # forced stop (SIGKILL) — last resort
```

**Sockets and ports.** A listening service owns a port:

```bash
ss -ltnp                   # listening TCP sockets and their processes
ss -ltnp | grep :8000
```

**Logs beat guesses.**

```bash
journalctl -u orders-api -n 50 --no-pager   # a service managed by systemd
journalctl -u orders-api -f                 # follow
tail -n 100 /var/log/app/app.log
```

**Disk and memory.**

```bash
df -h          # filesystem usage — a full disk breaks many things
du -sh /var/log/* | sort -h | tail
free -h        # memory and swap
```

**Worked example: "orders-api will not start".** Work from the outside in, one tool per question:

| Question | Command | Reading the output |
| --- | --- | --- |
| Is it running at all? | `systemctl status orders-api` or `ps -o pid,user,cmd -C orders-api` | `inactive (failed)` or no process: it exited. |
| Why did it exit? | `journalctl -u orders-api -n 50 --no-pager` | A line such as `PermissionError: /etc/orders/app.conf` or `Address already in use`. |
| Can its user read the config? | `ls -l /etc/orders/app.conf` and `id app` | Owner `alice`, mode `600`, service user `app`: `app` cannot read it. |
| Is the port taken? | `ss -ltnp \| grep :8000` | Another PID already listens on 8000. |
| Is the disk full? | `df -h /var` | `100%` explains failed log writes and many strange errors. |
| Is memory exhausted? | `free -h` and `journalctl -k \| grep -i 'out of memory'` | `Out of memory: Killed process` means the kernel killed it. |

**Reading permissions properly.** The ten characters of `-rw-r-----` are: file type (`-` file, `d` directory, `l` link), then three triples for owner, group and others. Numeric modes add `r=4`, `w=2`, `x=1`, so `640` means owner `rw-`, group `r--`, others `---`. For a directory, `x` means "may enter", so a file in `/etc/orders/` is unreachable if the directory itself is `700` and owned by someone else. `ls -ld /etc/orders` checks this.

```bash
id app                       # uid=998(app) gid=998(app) groups=998(app)
ls -l /etc/orders/app.conf   # -rw------- 1 alice alice ...
sudo chown root:app /etc/orders/app.conf
sudo chmod 640 /etc/orders/app.conf     # root may write, app may read, others nothing
sudo -u app cat /etc/orders/app.conf >/dev/null && echo readable
```

**Signals.** `kill` sends a signal. SIGTERM (15, the default) asks the process to shut down, letting it finish requests and close files. SIGKILL (9) cannot be caught, so the process cannot clean up; use it only if SIGTERM is ignored. Systemd and container runtimes send SIGTERM first for the same reason.

**Joining port, process and response.**

```bash
ss -ltnp | grep :8000
# LISTEN 0 128 0.0.0.0:8000 0.0.0.0:* users:(("python3",pid=1234,fd=5))
ps -o pid,ppid,user,cmd -p 1234
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health
```

`0.0.0.0:8000` means all interfaces; `127.0.0.1:8000` means only the local machine. Seeing which one is bound explains many "works locally, not remotely" reports.

**Where logs live.** Services managed by systemd write to the journal: `journalctl -u <unit>`. Many applications also write plain files under `/var/log`. Containers write to stdout and stderr, collected by the runtime. Check the most recent entries first, and note the timestamp of the failure so you can find the matching line.

**Disk and memory, quickly.** `df -h` shows filesystem usage by mount; `du -sh /var/log/* | sort -h | tail` finds what is large. `free -h` shows memory; the "available" column, not "free", is what matters, because Linux uses spare memory for caching.

**Common mistakes**

- Running `chmod 777` to make a permission error vanish. It fixes the symptom for everyone, including attackers.
- Editing a file as root, which then changes its owner and breaks the service user's access.
- Using `kill -9` first, leaving lock files or half-written data.
- Looking at the wrong log, or at logs older than the failure.
- Forgetting that `sudo` commands run as root and so hide permission problems the service user will hit.

**Exercise.** Start any small server on port 8000. Use `ps`, `ss` and `curl` to connect process id, port and response. Stop it and note how each tool's output changes.

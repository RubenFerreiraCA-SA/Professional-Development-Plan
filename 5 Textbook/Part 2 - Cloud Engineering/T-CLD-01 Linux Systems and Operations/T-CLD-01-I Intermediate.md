# T-CLD-01-I — Intermediate Practice

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-i"></a>
#### T-CLD-01-I — Intermediate Practice

**Users, groups and least privilege for services.** Run each service as its own unprivileged user:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin orders
sudo install -o root -g orders -m 0640 /dev/null /etc/orders/db.env
```

Give the service group read access to its configuration and nothing more. Check effective access with `sudo -u orders cat /etc/orders/db.env`.

**systemd units.**

```ini
[Unit]
Description=Orders API
After=network-online.target
Wants=network-online.target

[Service]
User=orders
Group=orders
EnvironmentFile=/etc/orders/db.env
ExecStart=/opt/orders/bin/orders-api --port 8000
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/orders
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now orders-api
systemctl status orders-api
journalctl -u orders-api --since "10 min ago"
```

**Finding what a process is doing.**

```bash
ls -l /proc/<pid>/fd | head        # open files and sockets
cat /proc/<pid>/cmdline | tr '\0' ' '
lsof -p <pid> | head
strace -f -p <pid> -e trace=network   # (diagnostic; may need privileges)
```

**Resource pressure symptoms**

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Writes fail, services crash | Disk or inode exhaustion | `df -h`, `df -i`, `du` |
| Process killed without a log line | Out-of-memory killer | `dmesg -T \| grep -i oom`, `journalctl -k` |
| High load, low CPU use | I/O wait | `vmstat 1`, `iostat -x 1` |
| "Too many open files" | File-descriptor limit | `ulimit -n`, unit `LimitNOFILE` |

**Package and update hygiene.** Install from trusted repositories, pin versions in images, apply security updates on a schedule and record what runs on each host (`dpkg -l` or `rpm -qa`).

**A Linux triage sequence**

1. Is the process running? (`systemctl status`, `ps`)
2. Is it listening where expected? (`ss -ltnp`)
3. What do its logs say? (`journalctl -u …`)
4. Can it read its configuration and write its data? (`namei -l path`, `sudo -u user test -r file`)
5. Is the machine under pressure? (`df`, `free`, `vmstat`)
6. Is the dependency reachable? (hand to T-CLD-02)

**Exercise.** Create the service user and a unit file for a toy program, deliberately make its configuration file unreadable, read the failure in the journal, fix the permission correctly and restart.

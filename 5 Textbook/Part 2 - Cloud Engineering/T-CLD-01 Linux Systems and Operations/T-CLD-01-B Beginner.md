# T-CLD-01-B — Beginner Foundations

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-b"></a>
#### T-CLD-01-B — Beginner Foundations

## Why this matters

Most cloud workloads, in virtual machines or containers, run on Linux. When a service misbehaves, the cause is almost always one of a short list: the process is not running, it cannot read or write something it needs, it is not listening where clients expect, a resource such as disk or memory has run out, or a dependency is unreachable. Linux can show you each of these, provided you know which command asks which question.

This section teaches the working vocabulary of a Linux terminal and one habit above all: **observe first, change second**. It covers the shell, files and paths, permissions, users and groups, processes, environment variables, streams and pipes, and packages. A fully guided session at the end uses a throwaway directory, so nothing you type can harm your machine.

Assumptions: you have a Linux shell (laptop, virtual machine, WSL or a cloud instance you may use) and an ordinary, unprivileged account. The examples use a fictional service called `orders-api`; nothing depends on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.

## First principles: what the operating system does for you

The **kernel** owns the hardware and hands out memory, CPU time, files and network connections. Everything else you touch is **user space**: the shell, `ls`, `curl`, your web server. Two ideas explain most Linux behaviour:

1. **Everything is mediated by the kernel.** A program does not read a disk; it asks the kernel to open a file and receives a small number, a *file descriptor*. Because every request passes through the kernel, permissions can be checked on every request.
2. **Most things look like files.** Regular files, directories, devices, pipes, sockets and live process information (under `/proc`) are all reached through paths and descriptors, which is why `ls`, `cat` and `grep` work on so many things.

| Concept | What it is | Example |
| --- | --- | --- |
| Process | A running program with a PID, an owner and open files | One `orders-api` worker, PID 1234 |
| File descriptor | A number naming something a process has open | 0 input, 1 output, 2 errors |
| User and group | The identities the kernel compares with permissions | `alice`, `app`, group `orders` |
| Path | A name for a place in the one directory tree rooted at `/` | `/etc/orders/app.conf` |

There are no drive letters. Extra disks are *mounted* at directories inside the single tree.

## The shell and the terminal

A **terminal** shows text and sends keystrokes; a **shell** (usually `bash`) reads a line, finds the program and starts it. In `ls -l /tmp` the shell sees the command `ls`, the *option* `-l` and the *argument* `/tmp`.

```bash
echo "$SHELL"          # which shell is configured
type cd                # cd is a shell builtin: it must change the shell's own directory
command -v curl        # which program would run?
man ls                 # documentation (/ searches, q quits); also: ls --help
```

Habits worth building: Tab completes names; `Ctrl-R` searches history; `Ctrl-C` interrupts a command; quote anything containing spaces (`ls "My Documents"`) because the shell splits words on spaces. A prompt ending in `$` normally means an ordinary user and `#` means root, a reminder that no safety net exists.

## Files and paths

A path beginning with `/` is **absolute**; any other is **relative** to the working directory. `.` is the current directory, `..` its parent and `~` your home.

```bash
pwd                    # where am I?
ls -la                 # long listing including hidden names (those starting with .)
cd /var/log; cd ..; cd ~; cd -      # absolute, up, home, back to previous
mkdir -p lab/notes     # -p creates parents and tolerates existing directories
cp a.txt b.txt; mv b.txt lab/notes/    # copy; move or rename
rmdir lab/notes        # removes an EMPTY directory only (a safe check)
less file.txt          # page through (q quits)
tail -n 20 file.txt    # last lines; tail -f follows new ones
stat file.txt          # size, owner, mode, timestamps
```

| Directory | Purpose | Why you look there |
| --- | --- | --- |
| `/etc` | System-wide configuration | A service reads the wrong setting |
| `/var/log` | Log files | Anything fails |
| `/var/lib` | Data owned by services | Where a database keeps files |
| `/tmp` | Temporary files, may vanish at reboot | Scratch only, never secrets |
| `/proc` | Live kernel and process data as files | Inspecting a running process |

**Deleting is final.** `rm` has no undo. List with the same pattern before you remove it, and never use `rm -r` with a path built from a variable that could be empty; `rm -rf "$DIR/"` with an empty `DIR` becomes `rm -rf /`.

A **symbolic link** is a small file holding a path; `ls -l` shows it with an arrow. Release directories commonly use one as a "current" pointer, and a *broken* link points at something that no longer exists.

```bash
ln -s /opt/orders/releases/2024-06-01 /opt/orders/current
ls -l /opt/orders/current      # lrwxrwxrwx ... current -> /opt/orders/releases/2024-06-01
find /var/log -name '*.log' -mtime -1     # log files changed in the last day
grep -n "ERROR" app.log                   # matching lines with numbers (-v inverts, -c counts)
```

## Permissions, users and groups

Every file has an owner, a group and three permission sets (owner, group, others), each allowing read (`r`), write (`w`) and execute (`x`).

```bash
ls -l secret.txt
# -rw------- 1 alice alice 20 Mar  1 10:00 secret.txt
```

Decode `-rw-r-----`: the type (`-` file, `d` directory, `l` link), then owner `rw-`, group `r--`, others `---`. Numeric modes add `r=4`, `w=2`, `x=1`, so `640` is owner 6, group 4, others 0.

| Mode | Use |
| --- | --- |
| `600` | Private keys and personal secrets |
| `640` | Config readable by one service group |
| `644` | Public readable files |
| `750` | A directory a service group may enter |
| `755` | Programs and shared directories |

On a **directory**, `r` lists names, `w` creates or deletes entries and `x` allows entering and reaching things inside. A file inside `/etc/orders/` is unreachable if that directory is `700` and owned by someone else, however open the file itself is. `namei -l /etc/orders/app.conf` shows every component of a path with its owner and mode.

```bash
chmod 600 secret.txt        # owner read/write only
chmod u+x deploy.sh         # add execute for the owner
chown app:app app.conf      # change owner and group (needs privilege)
id app                      # uid, gid and groups of an account
getent group orders         # who is in a group
sudo -u app cat /etc/orders/app.conf     # test access AS the service account
```

A process carries the identity of the user who started it. A service running as `app` cannot read a `600` file owned by `alice`: `Permission denied`. The fix is to give the right owner or group access, never `chmod 777`. `root` (UID 0) bypasses most checks, and `sudo` runs one command with root's or another user's rights. Testing with `sudo -u <service-user>` is more informative than plain `sudo`, because plain `sudo` runs as root and hides the exact problem the service will hit.

## Processes

A process has a PID, a parent (PPID), an owner, a state and open files. PID 1 is started by the kernel, usually `systemd`, and every other process descends from it.

```bash
ps -eo pid,ppid,user,stat,cmd | head      # snapshot
ps -o pid,ppid,user,cmd -p 1234           # one PID
pgrep -a python                           # find by name
top                                       # live view (q quits)
```

In the `STAT` column: `R` runnable, `S` sleeping (normal), `D` uninterruptible sleep (usually waiting on storage; cannot be killed until the wait ends), `Z` zombie (finished, not yet collected by its parent), `T` stopped. Append `&` to a command to run it in the background of your shell; services belong under `systemd`, not `&`.

`kill` sends a **signal**, which is not always a kill:

| Signal | Number | Meaning | Can the process handle it? |
| --- | --- | --- | --- |
| `SIGTERM` | 15 | Shut down cleanly (the default) | Yes: finish requests, close files |
| `SIGINT` | 2 | Interrupt (`Ctrl-C`) | Yes |
| `SIGHUP` | 1 | Terminal closed; daemons often reload | Yes |
| `SIGKILL` | 9 | Remove immediately | No: no cleanup, locks may remain |

An **exit code** says how a command ended: `0` is success, anything else is failure. `echo $?` prints the previous command's code. A process ended by signal N usually reports `128 + N`, so `137` is `SIGKILL` and `143` is `SIGTERM`.

## Environment variables, streams and pipes

An **environment variable** is a named string inherited by programs the shell starts (`PATH`, `HOME`, often `DATABASE_URL`).

```bash
echo "$PATH"                   # directories searched for programs, separated by :
MODE=debug ./run.sh            # set for ONE command
export MODE=debug              # set for this shell and its children; unset MODE removes it
```

A variable set without `export` does not reach child programs; a child cannot change its parent's environment. `PATH` order matters, since the first match wins (`type -a name` shows candidates). Secrets in environment variables are common but not hidden: the same user and root can read `/proc/<pid>/environ`.

Every process has three **streams**: standard input (0), output (1) and error (2). Errors travel separately so you still see them when output is redirected.

```bash
ls /etc/orders  > out.txt            # stdout to a file (overwrites; >> appends)
ls /nonexistent 2> err.txt           # stderr to a file
ls /etc /nonexistent > all.txt 2>&1  # both to one file (order matters)
ls /nonexistent 2>/dev/null          # discard errors; /dev/null swallows anything
```

A **pipe** (`|`) feeds one command's output to the next, so small tools combine into answers:

```bash
journalctl -u orders-api -n 500 --no-pager | grep -c ERROR       # errors in the last 500 lines
du -sh /var/log/* 2>/dev/null | sort -h | tail -5                 # the five largest log items
```

A pipeline's exit code is that of its **last** command; an earlier failure is hidden unless a script sets `set -o pipefail`.

## Packages, services and the first network checks

A **package manager** installs software with its dependencies, records what is installed and verifies signatures: `apt`/`dpkg` on Debian and Ubuntu, `dnf`/`rpm` on the Red Hat family.

```bash
dpkg -S /usr/bin/curl          # which package owns this file? (Red Hat: rpm -qf)
apt-cache policy curl          # installed and candidate versions
sudo apt install --no-install-recommends curl     # a change: read what it will add first
```

Rules: install from the distribution's repositories, read the proposed changes before confirming, and never pipe an unknown script from the internet into `sudo sh`. Software installed outside the package manager is invisible to update tools, so write down what you added.

A **service** is a background process; on most systems `systemd` supervises it and collects its output in the **journal**. A listening service owns a **port**.

```bash
systemctl status orders-api                  # state, main PID, recent log lines
journalctl -u orders-api -n 50 --no-pager    # last 50 lines; add -f to follow
ss -ltnp | grep :8000                        # who listens on 8000?
# LISTEN 0 128 0.0.0.0:8000 0.0.0.0:* users:(("python3",pid=1234,fd=5))   (illustrative)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health
df -h; df -i; free -h                        # disk blocks, inodes, memory
```

`0.0.0.0:8000` means all interfaces; `127.0.0.1:8000` means only this machine, which explains many "works locally, not remotely" reports. In `free -h`, read **available**, not "free": Linux uses spare memory as a cache and gives it back on demand. A restart is a change that can erase evidence, so read status and logs before you use it.

## A fully guided, safe terminal session

This session uses only a new directory under your home. Nothing needs `sudo` and nothing touches system files. Type each command yourself, read the expected result, and if yours differs, stop and work out why. Run it as an ordinary user, not root.

**Step 1 — Who and where.**

```bash
whoami
id
pwd
```

Expect your user name, numeric IDs with group names and your home directory.

**Step 2 — Create the sandbox.**

```bash
mkdir -p ~/linux-lab/etc ~/linux-lab/data ~/linux-lab/logs
cd ~/linux-lab
ls -la
```

Expect three directories plus `.` and `..`. You will remove only this directory at the end.

**Step 3 — Create files with redirection.**

```bash
echo "port=8000" > etc/app.conf
echo "db_password=example-not-a-real-secret" > etc/db.env
printf 'line one\nline two ERROR bad\nline three\n' > logs/app.log
ls -l etc logs
```

`>` overwrites, so repeating a command does not add lines. The new files are probably world-readable, which is wrong for a secret.

**Step 4 — Tighten permissions, then break and repair them.**

```bash
chmod 600 etc/db.env
chmod 644 etc/app.conf
chmod 750 data
stat -c '%a %U:%G %n' etc/db.env etc/app.conf data
chmod 000 etc/db.env
cat etc/db.env; echo "exit code: $?"
chmod 600 etc/db.env
cat etc/db.env
```

Expect `600`, `644` and `750` with your own name as owner and group. The first `cat` fails with `Permission denied` and a non-zero code even though you own the file, because the owner bits are zero. Restoring `600` repairs it precisely.

**Step 5 — Search and filter.**

```bash
grep -n "ERROR" logs/app.log
grep -c "line" logs/app.log
find . -type f -name '*.conf'
```

Expect one matching line (number 2), a count of 3 and one `.conf` path.

**Step 6 — Streams and pipes.**

```bash
ls etc nosuchdir
ls etc nosuchdir > out.txt 2> err.txt
cat out.txt; cat err.txt
cat logs/app.log | grep line | wc -l
```

The first command mixes a listing and an error; the second separates them into two files; the pipeline prints 3.

**Step 7 — Run a process, watch it, stop it.**

```bash
sleep 300 &
echo "background PID: $!"
ps -o pid,ppid,stat,etime,cmd -p $!
kill $!
sleep 1
jobs
```

Expect a PID and a line with state `S` and your shell as parent. After `kill`, the job is reported as `Terminated` (the shell may print this at the next prompt). It ended by `SIGTERM`, which in a script would show as exit status 143.

**Step 8 — Environment scope.**

```bash
GREETING=hello bash -c 'echo "child sees: $GREETING"'
echo "parent sees: [$GREETING]"
export LAB_MODE=training
bash -c 'echo "child sees: $LAB_MODE"'
unset LAB_MODE
```

The first child sees the one-command value, the parent sees nothing, and `export` lets the second child see its value until you `unset` it.

**Step 9 — Join process, port and response.** This uses Python's built-in web server; if `python3` is missing, skip to step 10.

```bash
cd ~/linux-lab/data
python3 -m http.server 8000 --bind 127.0.0.1 > ../logs/server.log 2>&1 &
SERVER_PID=$!
sleep 1
ss -ltnp | grep :8000
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8000/
ps -o pid,user,cmd -p "$SERVER_PID"
kill "$SERVER_PID"
sleep 1
ss -ltnp | grep :8000 || echo "nothing listens on 8000"
curl -s -o /dev/null http://127.0.0.1:8000/ || echo "curl failed with status $?"
cd ~/linux-lab
```

Expect `ss` to show `127.0.0.1:8000` with the same PID as `ps`, and `HTTP 200`. After the kill, `ss` shows nothing and `curl` exits with status 7. "Connection refused" means the machine answered but nothing listens: the signature of a stopped service, not of a firewall or a missing host.

**Step 10 — Read machine health, read-only.**

```bash
df -h .
free -h
uptime
ps -eo pid,user,pmem,cmd --sort=-pmem | head -5
```

Expect free space for your filesystem, memory with an "available" figure, three load averages and the five largest memory users. Nothing changes.

**Step 11 — Clean up exactly what you made.**

```bash
cd ~
ls linux-lab
rm -r linux-lab
ls linux-lab 2>&1
```

You list first, aim `rm -r` at one explicit name (no variable, no wildcard) and confirm the directory is gone. Every change happened in a place you control.

## A first diagnosis: "orders-api will not start"

Work from the outside in, asking one question per tool:

| Question | Command | Reading the output |
| --- | --- | --- |
| Is it running? | `systemctl status orders-api` | `failed` or `inactive`: it exited |
| Why did it exit? | `journalctl -u orders-api -n 50 --no-pager` | `PermissionError: /etc/orders/app.conf` or `Address already in use` |
| Can its user read the config? | `ls -l /etc/orders/app.conf`, `id app`, `namei -l …` | Owner `alice`, mode `600`, service user `app`: denied |
| Is the port taken? | `ss -ltnp \| grep :8000` | Another PID already listens |
| Is the disk full? | `df -h /var`, `df -i /var` | `100%` explains failed writes |
| Was it killed for memory? | `journalctl -k \| grep -i 'out of memory'` | `Out of memory: Killed process` |

The permission case, resolved precisely rather than with `777`:

```bash
ls -l /etc/orders/app.conf       # -rw------- 1 alice alice ...
sudo chown root:app /etc/orders/app.conf
sudo chmod 640 /etc/orders/app.conf      # root writes, app reads, others nothing
sudo -u app cat /etc/orders/app.conf >/dev/null && echo readable
```

The last line proves the fix as the identity that matters. Only then does a restart make sense.

## What can go wrong: common mistakes and how they look

| Mistake | How it shows up | Safer habit |
| --- | --- | --- |
| `chmod 777` to silence an error | Symptom vanishes; every account can now change the file | Set exactly the owner, group and mode the service needs |
| Editing a config as root | File becomes `root:root`; service loses access | Check `ls -l` after editing |
| `kill -9` first | Lock files and half-written data remain | `kill` first, wait, then escalate with a reason |
| Reading an old or wrong log | You "find" last week's error | Note the failure time; use `--since` |
| Unquoted paths with spaces | `rm` receives two arguments | Quote `"$name"`; list before deleting |
| Running a copied command unread | Unexpected deletion or privilege change | Read every word; try it in a sandbox first |
| Treating "free" memory as remaining memory | False alarm | Read "available" |

## Knowledge consolidation

- The **kernel** checks permissions on every request; user-space programs run with a user identity.
- The tree starts at `/`; know `/etc`, `/var/log`, `/var/lib`, `/tmp` and `/proc` by purpose.
- Permissions are owner, group and others times read, write and execute; directories use `x` for "may enter". `namei -l` explains unreachable paths.
- Services get their own unprivileged account; test with `sudo -u <account>`, not plain `sudo`.
- `kill` sends `SIGTERM` by default; `SIGKILL` is the last resort; 137 means `SIGKILL` and 143 means `SIGTERM`.
- Variables reach child processes only if exported, and they are not a hiding place for secrets.
- Streams are 0, 1 and 2; a pipeline reports its last command's status unless `pipefail` is set.
- `ss -ltnp` joins port, process and bind address; "connection refused" means nothing is listening.
- Read "available" memory; check `df -h` and `df -i`; read logs for the right time window.
- Observe first, change second, verify every change.

## Exercises

**Exercise 1 — Repeat the session without the guide.** Rebuild the sandbox from memory, set the same modes and prove each with `stat`. Write down which step you forgot.

**Exercise 2 — Predict permissions.** Predict whether `bob` (group `staff`, not the owner) can read each file, then check with `namei -l` or `sudo -u bob`: (a) mode `640`, group `staff`; (b) mode `640`, group `ops`; (c) mode `644` inside a `700` directory owned by `alice`; (d) mode `600` owned by `bob`.

**Exercise 3 — Bind address.** Start a server on port 8000 bound to `127.0.0.1`, then to `0.0.0.0`. Record what changes in `ss -ltnp` and what each would mean for a remote client.

**Exercise 4 — Redirection order.** Run `ls /etc /nonexistent` with `> both.txt 2>&1` and then with `2>&1 > both.txt`. Explain the difference in where the error text goes.

**Exercise 5 — Diagnose a fault you create.** In the sandbox write `serve.sh` that reads `etc/db.env`, remove read permission from the file, read the error, identify owner and mode with `ls -l`, and restore the least permission that works.

**Solution notes.**

*Exercise 2.* (a) Readable: `bob` is in `staff` and the group bits are `r--`. (b) Denied: `bob` is not in `ops` and others have nothing. (c) Denied: `bob` cannot enter a `700` directory owned by `alice`, so the path is unreachable; `namei -l` shows the `drwx------` component. (d) Readable: the owner bits apply first and `bob` is the owner. The kernel picks one class (owner, else group, else others) and uses only that class's bits.

*Exercise 3.* Bound to `127.0.0.1`, `ss` shows the loopback address only, so local `curl` works and remote clients are refused. Bound to `0.0.0.0`, remote clients can connect unless a firewall or cloud rule blocks them.

*Exercise 4.* With `> both.txt 2>&1`, stdout goes to the file, then stderr is pointed where stdout now goes, so both land in the file. With `2>&1 > both.txt`, stderr is pointed at the terminal first and only then is stdout moved to the file, so the error still prints on screen. Redirections are applied left to right.

*Exercise 5.* The error is `Permission denied`. The least fix is `chmod 600 etc/db.env`; `chmod 777` would also work and would be wrong.

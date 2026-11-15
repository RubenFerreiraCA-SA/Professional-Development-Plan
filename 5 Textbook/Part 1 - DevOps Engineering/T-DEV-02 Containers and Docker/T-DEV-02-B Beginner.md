# T-DEV-02-B — Beginner Foundations

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-b"></a>
#### T-DEV-02-B — Beginner Foundations

## Why this matters

Every software team eventually meets the sentence "it works on my machine". The service runs on your laptop because your laptop happens to have the right language version, the right libraries, the right environment variables and the right file in the right place. A colleague's laptop, the test server and the production host each differ in some small way, and one of those small differences is enough to make the same code fail.

A container attacks that problem by packaging the program *together with everything it needs from the operating system's user space* — the language runtime, libraries, default configuration — and running it in a restricted environment. If the package is the same, the starting conditions are the same, wherever it runs. That is why containers sit underneath most modern delivery pipelines: CI builds an image once, and the same image is tested, scanned and deployed.

This Beginner section assumes you can use a terminal and have Docker (or a compatible engine such as Podman) installed. It does **not** assume you know Linux internals. The commands use a fictional service called `orders-api`; nothing here depends on any other course material.

## First principles: a container is a process, not a machine

Start with what a computer does when you run a program: the operating system *kernel* creates a **process**, gives it memory, lets it read files and open network connections. Normally a process can see every other process, the whole filesystem (subject to permissions) and the whole network.

A container is an ordinary process (or small tree of processes) started with three kinds of restriction:

1. **A private view.** The kernel is told to show the process its own filesystem root, its own list of processes, its own network interfaces and hostname. This feature is called *namespaces*.
2. **A budget.** The kernel is told how much CPU, memory and process count the process may consume. This feature is called *cgroups* (control groups).
3. **A reduced set of privileges.** Dangerous operations (loading kernel modules, changing the system clock, many raw system calls) are withheld.

Analogy, and its limit: a container is like a hotel room. Guests share the building (the kernel), but each gets a private room (filesystem, network view) with a metered electricity supply (cgroups). The analogy fails because hotel walls are built for the purpose, whereas container walls are *rules in a shared kernel*. If the building's structure has a flaw, every room is affected. We will return to that in the Professional and Expert sections.

| Mechanism | What it controls | Beginner mental model |
| --- | --- | --- |
| Namespaces | What the process can *see* | A private room |
| cgroups | What the process may *use* | A metered supply |
| Capabilities, seccomp | Which privileged operations remain possible | A list of forbidden actions |

## Containers, virtual machines and images

Three words are constantly confused. Separate them now.

| Concept | What it is | Has its own kernel? | Typical start time | Typical size |
| --- | --- | --- | --- | --- |
| Virtual machine (VM) | A whole emulated computer running a full operating system | Yes | Tens of seconds | Gigabytes |
| Container | A restricted process on the host's kernel | No — shares the host kernel | Around a second or less | Megabytes to a few hundred megabytes |
| Image | A read-only template from which containers are created | Not applicable — it is files and configuration | Not applicable | Megabytes to hundreds of megabytes |

Consequences worth remembering:

- A Linux container can only run Linux programs against a Linux kernel. On macOS and Windows, Docker quietly runs a small Linux VM and starts your containers inside it.
- Because containers share the host kernel, a kernel flaw can affect all of them. A VM is a stronger isolation boundary. Containers are cheaper; VMs are sturdier. Neither is "better" in general.
- The *image* is the recipe-plus-ingredients; the *container* is a meal being cooked from it. You can start ten containers from one image.

You can see for yourself that a container is a host process:

```bash
docker run -d --name web nginx:1.27
docker top web                                   # the container's processes, as the host sees them
docker inspect -f '{{.State.Pid}}' web           # the process ID on the host
ps -o pid,cmd -p "$(docker inspect -f '{{.State.Pid}}' web)"   # the same process via ordinary ps (Linux host)
docker rm -f web
```

The "container" has a process ID on the host. There is no separate machine.

## Layers: how an image is built from reusable pieces

An image is not one big file. It is an ordered stack of **layers**, each a set of filesystem changes (files added, modified or deleted), plus a small JSON configuration describing the default command, environment variables and user.

```text
  Top    ─ layer 5: COPY . .              (your source code)       changes often
           layer 4: RUN pip install ...   (your dependencies)      changes sometimes
           layer 3: WORKDIR /app
           layer 2: Python runtime and libraries                   changes rarely
  Bottom ─ layer 1: minimal Debian base                            changes rarely
```

Why layers matter in daily work:

- **Sharing.** Two images that start from the same base reuse the same stored base layers. You download and store them once.
- **Caching.** When you rebuild, Docker reuses every layer whose instruction and inputs have not changed. A change in one layer invalidates that layer *and every layer above it*.
- **Immutability.** Layers are read-only. A running container gets one thin **writable layer** on top; anything the container writes goes there and disappears when the container is removed.
- **Permanence.** Layers are content that anyone with access to the image can extract. Deleting a file in a later layer hides it but does not remove it from the earlier one. This is why a secret copied into an image is a leaked secret.

```bash
docker pull python:3.12-slim
docker history python:3.12-slim        # each layer and the instruction that made it
```

## Registries, tags and digests

A **registry** is a server that stores and distributes images — Docker Hub, a cloud provider's registry, or one your organisation runs. `docker pull` downloads from a registry; `docker push` uploads to one. An image reference has the shape:

```text
registry.example.com/team/orders-api:1.4.2
└──── registry ─────┘└─ repository ─┘└ tag ┘
```

If the registry is omitted, Docker Hub is assumed, and if the tag is omitted, `latest` is assumed. Two ways to name an image:

| Name | Example | Property |
| --- | --- | --- |
| Tag | `python:3.12-slim` | Human-friendly, **movable**: the publisher can point it at a new image tomorrow |
| Digest | `python@sha256:<64 hex characters>` | A hash of the content: **immutable**, identifies exactly one image |

`latest` is only a tag with a convenient name — it does not mean "newest" or "safest", and it can change under you. Builds that depend on `latest` are not repeatable. For learning, pin a specific version tag. For releases (Professional section), deploy by digest.

## Vocabulary in context

| Term | Meaning in practice |
| --- | --- |
| Image | Immutable template: layers plus configuration (default command, environment, user). |
| Container | A running (or stopped) instance of an image with a thin writable layer. |
| Dockerfile | A text file of build instructions that produces an image. |
| Build context | The directory sent to the builder; anything in it *can* be copied into the image. |
| `.dockerignore` | List of paths excluded from the build context (for example `.git`, `.env`). |
| Registry | Server that stores and serves images. |
| Tag / digest | A movable name for an image / a content hash that identifies it exactly. |
| `ENTRYPOINT` / `CMD` | The program the container runs, and its default arguments. |
| Volume | Storage managed outside the container's writable layer; survives container removal. |
| Bind mount | A host directory mapped into the container; convenient for development. |
| Network | A virtual network containers join; containers on the same user-defined network reach each other by name. |
| Published port | A host port forwarded to a container port (`-p host:container`). |

## The first commands

```bash
docker run --rm -p 8080:80 nginx:1.27      # run, publish a port, remove container on exit
docker ps                                   # running containers
docker ps -a                                # running and stopped containers
docker logs <container>                     # standard output and standard error
docker exec -it <container> sh              # open a shell inside a running container
docker stop <container>                     # SIGTERM, then SIGKILL after a grace period
docker images                               # local images
```

Open `http://127.0.0.1:8080` in a browser while the first command is running and you will see the web server's welcome page. Press `Ctrl-C` to stop it; `--rm` removed the container on exit.

Flags used above, in plain language:

- `-d` — run in the background (detached), print the container ID.
- `-it` — give the process an interactive terminal (needed for a shell).
- `--rm` — delete the container when it exits, so it does not accumulate.
- `--name` — give the container a name you can type instead of a random ID.
- `-p 8080:80` — forward host port 8080 to container port 80.

## A guided first Dockerfile

We will containerise a tiny web service. The application is deliberately minimal so the container, not the code, is the lesson.

Directory layout:

```text
orders-api/
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── main.py
```

`requirements.txt` (pin the versions you have tested; the ones below are examples):

```text
fastapi==0.115.0
uvicorn==0.30.6
```

`main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def orders():
    return [{"id": 1, "item": "keyboard"}]
```

`.dockerignore` — decide what must *never* enter the build context:

```text
.git
.env
.env.*
__pycache__/
.venv/
*.pem
*.key
```

`Dockerfile`, with an explanation for every instruction:

```dockerfile
# Start from an official, small Python image. Pin a version; never rely on :latest.
FROM python:3.12-slim

# Create /app if missing and make it the working directory for later instructions.
WORKDIR /app

# Copy ONLY the dependency list first. This layer changes rarely, so it caches well.
COPY requirements.txt .

# Install dependencies. --no-cache-dir keeps pip's download cache out of the layer.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code. This layer changes on every edit, so it comes last.
COPY . .

# Run as a numeric non-root user: a compromised app does not get root inside the container.
USER 10001

# Documentation only: tells readers which port the app intends to use. It publishes nothing.
EXPOSE 8000

# Exec form (JSON array): the app is PID 1 and receives SIGTERM directly.
# --host 0.0.0.0 is required; 127.0.0.1 would be unreachable through a published port.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run it:

```bash
docker build -t orders-api:local .
docker run -d --name orders --rm -p 8000:8000 orders-api:local
curl -fsS http://127.0.0.1:8000/health
docker logs orders
docker stop orders
```

Illustrative output of the `curl` step (your exact text depends on your app):

```text
{"status":"ok"}
```

Annotated reading of the command lines:

- `-t orders-api:local` names and tags the resulting image. The final `.` is the *build context* — the current directory.
- `-d` runs in the background; `--rm` removes the container after it stops; `--name orders` gives it a handle.
- `curl -fsS` fails on HTTP errors (`-f`), stays quiet except for errors (`-sS`).

## Build, run, stop, logs: the everyday loop

1. Edit the code.
2. `docker build -t orders-api:local .` — the layer cache makes this fast when only code changed.
3. `docker run ...` — start a container from the new image.
4. `docker logs -f <container>` — follow the output (`-f` follows; `Ctrl-C` stops following but not the container).
5. `docker stop <container>` — ask the process to finish.
6. Repeat.

**Why the output goes to logs.** Containers are expected to write their logs to standard output and standard error. Docker collects them so `docker logs` works. If an application writes logs only to a file inside the container, `docker logs` shows nothing and the file vanishes with the container.

**Layer cache, demonstrated.** Run `docker build` twice without changing anything: each step reports `CACHED`. Now edit `main.py` and rebuild: only the `COPY . .` layer and those after it run again; the slow `pip install` is cached. Swap the order of the two `COPY` lines and every edit reinstalls all dependencies. That one reordering is the most common beginner speed-up.

## Ports and networks

**Publishing a port.** `-p 8080:80` means "traffic to host port 8080 goes to container port 80". `EXPOSE` in a Dockerfile only documents intent. A server inside the container must listen on `0.0.0.0` (all interfaces). If it listens on `127.0.0.1`, only the container itself can reach it, and the published port appears to accept connections and then reset them.

**Whose `localhost`?** Inside a container, `127.0.0.1` is the container itself. It is not your laptop, and it is not the container next door. The first time your app says "connection refused" to a database on "localhost", this is the reason.

**Container-to-container traffic.** Put containers on a *user-defined network* and they reach each other by container name, using Docker's built-in DNS:

```bash
docker network create orders-net
docker run -d --name db --network orders-net \
  -e POSTGRES_PASSWORD=dev-only-password postgres:16-alpine
docker run --rm --network orders-net alpine:3.20 getent hosts db     # resolves "db" to a container IP
docker run --rm --network orders-net alpine:3.20 ping -c 1 db
docker rm -f db && docker network rm orders-net
```

Names work on user-defined networks; they do not work on the default `bridge` network. When two containers cannot find each other, ask first: *are they on the same user-defined network?*

Note the password above is for a disposable local container. Never put a real credential in a command you will paste into shared documentation or shell history.

## Volumes and bind mounts: keeping data

The writable layer disappears with the container. Prove it:

```bash
docker run --name scratch python:3.12-slim sh -c 'echo hi > /tmp/note'
docker rm scratch                       # /tmp/note is gone with the container

docker volume create orders-data
docker run --rm -v orders-data:/data python:3.12-slim sh -c 'echo hi > /data/note'
docker run --rm -v orders-data:/data python:3.12-slim cat /data/note     # prints: hi
docker volume ls                        # orders-data is still here
```

| Mechanism | Syntax | Use for | Survives `docker rm`? |
| --- | --- | --- | --- |
| Writable layer | (default) | Throwaway scratch files | No |
| Named volume | `-v orders-data:/data` | Database files, uploads | Yes, until the volume is removed |
| Bind mount | `-v "$(pwd)":/app` | Live-editing source in development | It is a host directory, so yes |

Rule of thumb: **anything that must outlive a container belongs in a volume or in an external service** (a managed database, object storage), never in the writable layer. Volumes are deleted only deliberately (`docker volume rm`, `docker volume prune`, `docker compose down -v`), and that deliberateness is why you should be careful with those commands.

## Inspecting and safely removing things

Containers, images, networks and volumes accumulate. Look before you delete.

```bash
docker ps -a                              # containers including stopped ones
docker images                             # images
docker volume ls                          # volumes
docker network ls                         # networks
docker system df                          # how much space images, containers and volumes use
docker inspect orders                     # full JSON detail for a container or image
docker inspect -f '{{.State.Status}} exit={{.State.ExitCode}}' orders
docker inspect -f '{{json .NetworkSettings.Networks}}' orders
docker diff orders                        # files changed in the writable layer
```

Remove deliberately:

```bash
docker rm <container>                     # remove a stopped container
docker rm -f <container>                  # stop and remove (kills if necessary)
docker rmi orders-api:local               # remove an image tag
docker container prune                    # remove ALL stopped containers
docker image prune                        # remove dangling images (untagged leftovers)
```

Danger list:

- `docker volume prune` and `docker compose down -v` delete **data**. Run `docker volume ls` and think before you do.
- `docker system prune -a` removes every image not used by a container; it is safe on a scratch machine and annoying elsewhere because everything must be pulled again.
- Do not run cleanup commands on a shared server because "the disk is full". Find out what owns the space with `docker system df` first.

## Running as non-root, and why it sometimes fails

`USER 10001` runs the app as an unprivileged numeric user. If the app then fails with `Permission denied`, the files it needs are owned by root. The fix is to give the app ownership of what it must write (`COPY --chown=10001:10001 . .`, or a writable volume) — not to go back to root.

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| No `.dockerignore`, then `COPY . .` | `.env` or keys appear in the image; builds are slow because the context is huge | Add `.dockerignore`; rotate any secret that was copied |
| Dependencies installed after `COPY . .` | Every code edit reinstalls everything | Copy the dependency file, install, *then* copy the source |
| Data in the writable layer | Data vanishes after `docker rm` or recreate | Use a named volume or external database |
| App listens on `127.0.0.1` | `curl` to the published port hangs or resets | Listen on `0.0.0.0` inside the container |
| `localhost` used to reach another container | "Connection refused" | Use a user-defined network and the container name |
| Shell-form `CMD python app.py` | `docker stop` takes ten seconds and the exit code is 137 | Use exec form `CMD ["python", "app.py"]` |
| Relying on `latest` | A rebuild next month behaves differently | Pin a version tag; later, a digest |
| Forgetting `--rm` | `docker ps -a` shows dozens of stopped containers | Use `--rm` for throwaway runs |
| Container exits immediately | `docker ps` shows nothing | `docker ps -a`, then `docker logs <name>` and check the exit code |
| Running a database container without a volume | Data lost on removal | Mount a volume at the database's data directory |

**Reading an exit code.** `docker inspect -f '{{.State.ExitCode}}' <c>` returns the code. 0 means normal exit; non-zero means failure; 137 means the process was killed with `SIGKILL` (128 + 9) — often an out-of-memory kill or a stop that timed out; 143 means it ended after `SIGTERM` (128 + 15), which is the *expected* code for a graceful stop of many programs.

## Knowledge consolidation

- A container is an **ordinary process** with a restricted view, a resource budget and fewer privileges; it shares the host kernel, so it is a weaker boundary than a VM.
- An **image** is a read-only stack of layers plus configuration; a **container** is a running instance with a thin writable layer that is lost on removal.
- **Layers** are cached from top to bottom; put slow, rarely changing steps first and frequently changing steps last.
- **Tags move; digests do not.** `latest` is only a name.
- **Volumes** keep data; **networks** with names connect containers; **published ports** connect the outside world.
- **Inside a container, `localhost` means the container.**
- Inspect before you remove; treat volume removal as data deletion.
- Anything copied into an image can be extracted by anyone who can pull it.

## Exercises

**Exercise 1 — Build and run.** Create the `orders-api` directory above. Build the image, run it with a published port, call `/health`, read the logs and stop the container. Write down the exact image ID (`docker images --no-trunc`) and the container's host PID while it ran.

**Exercise 2 — Prove the cache.** Build twice. Edit `main.py` and build again. Then swap the two `COPY` lines (put `COPY . .` before the install) and edit `main.py` again. For each of the four builds, note which steps said `CACHED` and which ran.

**Exercise 3 — Persistence.** Run a container that writes a file in `/tmp`, remove it and show the file is gone. Repeat with a named volume and show the file survives. Then remove the volume deliberately.

**Exercise 4 — Names and `localhost`.** Start `db` on a user-defined network as shown. From a second container on the same network resolve `db`. Then try the same from the default network and record what changes.

**Exercise 5 — The ten-second stop.** Run `docker run -d --name sleepy alpine:3.20 sleep 300` and time `docker stop sleepy` (`time docker stop sleepy`). Repeat with `docker run -d --init --name polite alpine:3.20 sleep 300`. Explain the difference.

**Solution notes.**

*Exercise 1.* Illustrative expectations: the image ID is a `sha256:` string; the host PID is a number from `docker inspect -f '{{.State.Pid}}' orders`; `docker logs` shows the server's start-up lines and one request line per `curl`. If `curl` fails, check in this order: is the container running (`docker ps`), is the port published (`docker ps` PORTS column), is the server listening on `0.0.0.0`?

*Exercise 2.* Build 2 should be fully `CACHED`. After editing `main.py` the `pip install` step should stay cached and only `COPY . .` onward should rerun. After you swap the order, the `pip install` step should rerun on every source edit, because the preceding layer's input changed. Exact timings vary; the pattern of `CACHED` lines is what to record.

*Exercise 3.* After `docker rm`, a new container from the same image should not contain `/tmp/note`. With a volume, a new container mounting `orders-data` should still read `/data/note`. `docker volume rm orders-data` should fail while a container still uses it, which is a useful safety property.

*Exercise 4.* On the user-defined network `getent hosts db` should print an address. On the default `bridge` network the name should not resolve, because built-in name resolution is a feature of user-defined networks. If it resolves in both, check which network the containers actually joined with `docker inspect`.

*Exercise 5.* Typically the first `docker stop` waits about ten seconds (the default grace period), then forcibly kills the process, and the exit code is 137. A process running as PID 1 in a container does not get the kernel's default signal handling, so a program such as `sleep`, which installs no handler, simply ignores `SIGTERM`. With `--init` a tiny init program becomes PID 1 and forwards the signal, so the stop is usually immediate. Treat these as results you should observe yourself; the Intermediate section explains PID 1 and signal handling properly.

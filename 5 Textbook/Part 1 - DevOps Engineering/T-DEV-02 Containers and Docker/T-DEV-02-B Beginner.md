# T-DEV-02-B — Beginner Foundations

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-b"></a>
#### T-DEV-02-B — Beginner Foundations

**What a container is.** A container packages a process (or process tree) with a filesystem view, resource limits and a network identity. Unlike a virtual machine it shares the host's kernel. Linux features create the isolation:

| Mechanism | What it controls |
| --- | --- |
| Namespaces | What the process can *see*: processes, mounts, network, hostname, users |
| cgroups | What the process may *use*: CPU, memory, I/O |
| Capabilities, seccomp, security modules | Which privileged operations remain possible |

**Images and containers.** An *image* is an immutable stack of filesystem layers plus configuration (entrypoint, environment, user). A *container* is a running instance: the image plus a thin writable layer. Delete the container and the writable layer disappears. Anything that must survive replacement belongs in a volume or an external service.

**First commands**

```bash
docker run --rm -p 8080:80 nginx:1.27      # run, publish a port, remove on exit
docker ps                                   # running containers
docker logs <container>                     # standard output and error
docker exec -it <container> sh              # a shell inside
docker stop <container>                     # SIGTERM, then SIGKILL after a grace period
docker images                               # local images
```

**A minimal Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t orders-api:local .
docker run --rm -p 8000:8000 orders-api:local
curl -fsS http://127.0.0.1:8000/health
```

**Why order matters.** Docker caches each instruction as a layer. Copy the dependency file and install dependencies *before* copying the rest of the source, so editing source does not reinstall dependencies.

**Localhost surprises.** Inside a container, `127.0.0.1` is the container itself, not your laptop and not another container. Containers on the same user-defined network reach each other by service name.

**Container versus virtual machine.** A virtual machine runs its own kernel on emulated hardware; a container is an ordinary process on the host's kernel with a restricted view. That is why containers start in about a second and use little memory, and also why a container is a weaker isolation boundary than a VM: a kernel bug affects all containers on the host. A Linux container cannot run a different operating-system kernel; on macOS and Windows, Docker runs a small Linux VM for you.

```bash
docker run -d --name web nginx:1.27
docker top web                      # the container's processes, as the host sees them
docker inspect -f '{{.State.Pid}}' web
ps -o pid,cmd -p $(docker inspect -f '{{.State.Pid}}' web)   # the same process on the host
```

The last command shows the point: the "container" is a host process with a PID.

**Image versus container, shown with commands.**

```bash
docker pull python:3.12-slim
docker history python:3.12-slim              # the layers and the instruction that created each
docker image inspect python:3.12-slim --format '{{json .Config.Entrypoint}} {{json .Config.Env}}'
docker run --name scratch python:3.12-slim sh -c 'echo hi > /tmp/note'
docker rm scratch                            # /tmp/note is gone with the writable layer
docker run --rm -v orders-data:/data python:3.12-slim sh -c 'echo hi > /data/note'
docker volume ls                             # the named volume survives container removal
```

Images are addressed by a tag (human-friendly, can move) or a digest (`@sha256:…`, immutable). Tags such as `latest` change over time, so builds that rely on them are not reproducible.

**More vocabulary**

| Term | Meaning |
| --- | --- |
| Registry | A server that stores and distributes images (Docker Hub, a cloud registry). |
| Tag / digest | A movable name for an image / a content hash that identifies it exactly. |
| Volume | Storage managed outside the container's writable layer, surviving removal. |
| Bind mount | A host directory mounted into the container, convenient for development. |
| `ENTRYPOINT` / `CMD` | The program to run, and its default arguments. |
| `.dockerignore` | Files excluded from the build context (for example `.git`, `.env`, `node_modules`). |
| Build context | The directory sent to the builder; everything in it can be copied into the image. |

**Layer cache, demonstrated.** Run `docker build` twice and the second build reports `CACHED` for each step. Edit one source file and rebuild: with dependencies installed before `COPY . .`, only the final layers rebuild. Swap the order and every edit reinstalls all dependencies. A change to any instruction invalidates that layer and every layer after it.

**Publishing a port.** `-p 8080:80` means host port 8080 forwards to container port 80. `EXPOSE` in a Dockerfile only documents the intended port; it does not publish anything. A server inside the container must listen on `0.0.0.0` to be reachable through a published port; listening on `127.0.0.1` makes it unreachable from outside.

**Running as non-root.** `USER 10001` means that a compromise of the app does not give root inside the container. If the app then fails with `Permission denied`, the files it needs are owned by root; fix ownership with `COPY --chown=10001 …` rather than going back to root.

**Common mistakes**

- Copying secrets into an image with `COPY . .` because `.dockerignore` was missing. Image layers can be extracted by anyone who can pull the image.
- Storing data in the container's writable layer and losing it on `docker rm`.
- Forgetting `--rm` and accumulating stopped containers (`docker ps -a` shows them).
- Using `localhost` to reach another container or the host. Use the service name on a user-defined network.
- Using the shell form `CMD python app.py`, which runs the app under `/bin/sh` and may stop it receiving `SIGTERM`; prefer the JSON form shown above.
- Treating `docker stop` taking ten seconds as normal. It means the process ignored SIGTERM.

**Exercise.** Build the image above for any small web app. Stop the container with `docker stop` and time it. If it takes about ten seconds, the process is ignoring `SIGTERM`; note that and revisit it in the Intermediate section.

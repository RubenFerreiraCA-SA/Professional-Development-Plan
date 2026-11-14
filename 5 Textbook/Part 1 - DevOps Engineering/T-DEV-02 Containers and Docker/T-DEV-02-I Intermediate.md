# T-DEV-02-I — Intermediate Practice

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-i"></a>
#### T-DEV-02-I — Intermediate Practice

**PID 1 and signals.** The first process in a container is PID 1. It receives signals differently from ordinary processes and is responsible for reaping orphaned children. If your application ignores `SIGTERM`, the runtime waits for the grace period and then sends `SIGKILL`, cutting off in-flight requests. Either handle `SIGTERM` in the application, or use a small init process (such as `tini`) as PID 1 to forward signals. Use the exec form of `CMD` (`["prog", "arg"]`) rather than the shell form, otherwise a shell becomes PID 1 and may not forward signals.

**Multi-stage builds.** Separate building from running. The build stage contains compilers and package managers; the runtime stage contains only what the service needs:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
RUN useradd --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels
COPY --chown=app:app app/ ./app/
USER app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add a `.dockerignore` (`.git`, `.env`, virtual environments, test output) so secrets and junk never enter the build context.

**Compose as a local contract.** Compose describes a multi-container application:

```yaml
services:
  api:
    build: ./app
    ports: ["8000:8000"]
    environment:
      DATABASE_HOST: db
      DATABASE_USER: orders
    env_file: [.env]               # gitignored, never committed
    depends_on:
      db: { condition: service_healthy }
    restart: unless-stopped
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: orders
      POSTGRES_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD in .env}
    volumes: [pg_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orders"]
      interval: 5s
      retries: 10
volumes:
  pg_data:
```

Notes: the database is not published to the host; the API reaches it as `db:5432`. `depends_on` with `service_healthy` waits for the database to accept connections once, but clients must still retry — readiness at start-up is not a permanent guarantee.

**Health versus readiness.** Provide separate endpoints. `/health` means the process is alive. `/ready` means dependencies work. A TCP connect to the database proves a listener exists, not that authentication and queries work; prefer a real `SELECT 1`. Test the readiness check by breaking the password on purpose and confirming the endpoint returns an error.

**Persistence options**

| Mechanism | Typical use | Survives container delete? |
| --- | --- | --- |
| Writable container layer | Temporary files | No |
| Named volume | Database files | Yes, until the volume is removed |
| Bind mount | Live-editing source in development | Depends on the host path |

**Diagnosis recipes.** "Connection refused" from the API to the database: check who `localhost` is, what the DNS name resolves to (`docker exec api getent hosts db`), and whether the database is healthy (`docker compose ps`, `docker compose logs db`). Container exits immediately: `docker logs`, then `docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' <c>`. Exit code 137 usually means `SIGKILL` — often an out-of-memory kill or a missed shutdown deadline.

**Exercise.** Run the Compose stack, stop `db`, observe what `/health` and `/ready` return, restart it, then delete and recreate the `api` container and confirm the volume kept the data.

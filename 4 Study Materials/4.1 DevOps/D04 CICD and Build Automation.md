# Chapter 4 — CI/CD and Build Automation (D04)

*DevOps Engineering textbook · Chapter 4 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D04 course detail](../../3%20Course%20Detail/3.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) for the current planning estimate (about 24–36 hours). |
| **Prerequisites** | [D01](D01%20Repository%20Fundamentals.md), [D02](D02%20Advanced%20Git.md), [D03](D03%20Docker%20and%20Containerization.md); comfort writing automated tests and using GitHub or GitLab. |

## How to study this chapter

Pipelines are a **platform product**. Your job is not “make green checks appear.” It is to convert an approved source change into a **traceable, tested, immutable artifact**, then promote that *same* artifact without rebuilding it for each environment.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where CI is easy to get wrong (untrusted pull requests, mutable tags, secrets), this chapter **shows a working sequence first**, then asks you to reproduce it, then adds a harder challenge.

Implementation examples use **GitHub Actions**. The design principles apply to GitLab CI and similar systems; where syntax differs, translate deliberately and note the difference in your ADR. This text teaches [D04 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D04 bar is: *a failing check blocks merge; a passing change yields a digest-addressed artifact traceable to the merge commit; promotion selects that digest (not a floating tag).*

> **Safety boundary:** Use a private training repository. Store only fabricated secrets in Actions secrets. Do not enable workflows that run untrusted fork PRs with write credentials. Prefer GHCR private packages or a disposable local registry for training publishes.

### Learning outcomes

1. Design fast, deterministic PR validation with actionable failure feedback.
2. Separate validation, release and promotion, and explain trust boundaries between them.
3. Apply least-privilege tokens, safe triggers and secret hygiene for untrusted code.
4. Publish container artifacts with commit SHA, image digest, SBOM/scan evidence.
5. Promote and roll back by **digest**, without rebuilding for each environment.
6. Extract a reusable pipeline component and apply it to a second service.
7. Diagnose code, test, runner, cache, security and promotion failures distinctly.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
test -f app/Dockerfile
test -f app/harbour_api/main.py
git status -sb
docker version
```

You need a GitHub (or GitLab) remote with permission to add workflows and branch protection. Local `act` is optional; provider-hosted runs are the evidence that counts for the assessment.

---

## Section 4.1 — Delivery architecture before YAML

### 4.1.1 The trust stages

Draw this flow and keep it visible while you build:

```text
untrusted change (PR)     trusted integration (main)     release          promote
---------------------     --------------------------     -------          -------
lint / unit / smoke  -->  same checks + build once  -->  immutable   -->  point env
no publish secrets        publish image + evidence       digest           at digest
```

| Stage | May run untrusted code? | May publish artifacts? | May deploy? |
| --- | --- | --- | --- |
| PR validation | Yes (isolated) | No | No |
| Post-merge release | Only from protected `main` | Yes (narrow token) | Optional / separate |
| Promotion | No application build | No rebuild | Yes (digest only) |

**Design choices to defend** (capture in `docs/decisions/0004-delivery-architecture.md` as you go):

- Trunk-based short-lived branches versus long-lived release branches
- Required checks versus optional decorative workflows
- Whether CD pushes live, or only updates desired-state that GitOps (D06) reconciles
- Fast tests on every PR; slower suites at merge or release

**Worked example — test matrix (fill durations with your measurements later):**

| Suite | Trigger | Approx duration | Failure impact | Owner |
| --- | --- | --- | --- | --- |
| Lint / format | PR + main | minutes | Blocks merge | App team |
| Unit tests | PR + main | minutes | Blocks merge | App team |
| Container smoke (`/health`) | PR (optional) / release | minutes | Blocks release | App + platform |
| Image scan | Release | minutes | Policy gate | Platform |
| Promotion | Manual or main | minutes | Env drift / outage | Platform |

**Practice:** Add one row for a test you are *not* running yet and state when it should enter the gate.

**Reflect:** If a scan finds a critical CVE with no fix, who may approve an exception, and when does it expire?

---

## Section 4.2 — Make Harbour testable in CI

CI cannot be deterministic if the app has no automated checks. Add a small unit test that does not require Postgres (keep DB integration for Compose/smoke).

### 4.2.1 Worked example — unit test for `/health` and `/info`

Create `app/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from harbour_api.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "harbour-api"


def test_info_includes_service():
    response = client.get("/v1/info")
    assert response.status_code == 200
    assert response.json()["service"] == "harbour-api"
```

Add test dependencies to `app/requirements.txt` (keep pins exact):

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
psycopg[binary]==3.2.4
httpx==0.28.1
pytest==8.3.4
```

`httpx` is required by FastAPI’s `TestClient` in current versions.

### 4.2.2 Worked example — run tests locally before wiring CI

```bash
cd "$HARBOUR_ROOT/app"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
deactivate
```

**Expected:** both tests pass. If imports fail, run pytest from `app/` so `harbour_api` is on `PYTHONPATH` (or set `PYTHONPATH=.`).

### 4.2.3 Deliberate regression (you will use this for the gate demo)

```bash
cd "$HARBOUR_ROOT/app"
# temporary break — do not leave this committed on main
printf '%s\n' 'def test_health_ok():' '    assert False, "deliberate regression"' > /tmp/broken_test_snippet.py
```

Better: edit `test_health.py` temporarily:

```python
def test_health_ok():
    assert False, "deliberate regression for CI gate demo"
```

Run `pytest -q` and confirm failure, then **restore the real assertion** before continuing. You will re-introduce the failure on a PR branch in Section 4.3.

Confirm `.venv/` stays ignored:

```bash
cd "$HARBOUR_ROOT"
git check-ignore -v app/.venv
git add app/tests app/requirements.txt
git status --short
git commit -m "test(app): add FastAPI health unit tests"
```

**Practice — reproduce:** From a clean shell, recreate the venv, install from `requirements.txt` only, and get a green `pytest -q`.

**Challenge:** Add a test that fails if `HARBOUR_COMMIT` is missing in a release-shaped environment variable set — without breaking local default runs.

---

## Section 4.3 — Pull request validation pipeline

### 4.3.1 Concept: deterministic installs and clean trees

PR CI should:

1. Install from **pinned** dependencies (`requirements.txt` pins; prefer a generated lockfile when you adopt `pip-tools` / `uv`)
2. Run lint/tests in a clean runner
3. Upload logs/reports even on failure
4. Fail the required check on regression
5. Never push images or use deployment secrets

### 4.3.2 Worked example — GitHub Actions validate workflow

Create `.github/workflows/harbour-validate.yml`. **Do not add path filters yet** — a required check that is skipped on docs-only PRs will block merges. Teach a reliable gate first; optimise later (Section 4.3.4).

Write generated reports under `${{ runner.temp }}`, not inside the checkout. Otherwise `pytest --junitxml=…` leaves an untracked file and a clean-tree check fails on a green test run.

```yaml
name: harbour-validate

on:
  pull_request:
  push:
    branches: ["main"]

permissions:
  contents: read

concurrency:
  group: harbour-validate-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: app
    steps:
      - name: Check out source
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: app/requirements.txt

      - name: Install dependencies (pinned)
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Unit tests
        run: pytest -q --junitxml="${{ runner.temp }}/pytest-report.xml"

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: harbour-pytest-${{ github.run_id }}
          path: ${{ runner.temp }}/pytest-report.xml

      - name: Fail if the tree was dirtied
        working-directory: ${{ github.workspace }}
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            echo "CI must not leave uncommitted changes:"
            git status --porcelain
            exit 1
          fi
```

Pin Actions by full commit SHA for production platforms; tags (`@v4`) are acceptable while learning if you document the risk and an upgrade plan.

Commit and push:

```bash
cd "$HARBOUR_ROOT"
mkdir -p .github/workflows
# write the file, then:
git add .github/workflows/harbour-validate.yml
git commit -m "ci: add Harbour PR validation workflow"
git push -u origin HEAD
```

Open the Actions tab and confirm a green run on `main` (including that the clean-tree step passes).

### 4.3.3 Worked example — failing check blocks merge

1. In the GitHub UI (or API), require the `harbour-validate` / `test` check before merging into `main` (branch protection or rulesets). Because the workflow runs on **every** PR (no path filter yet), docs-only PRs still get a green required check instead of a skipped one.
2. Create a branch that deliberately breaks the unit test:

```bash
cd "$HARBOUR_ROOT"
git switch -c demo/ci-gate-failure
# edit app/tests/test_health.py to assert False as shown earlier
git add app/tests/test_health.py
git commit -m "test: deliberate failure for gate demo"
git push -u origin HEAD
```

3. Open a pull request. Wait for the failed check.
4. Confirm the UI **blocks** merge (or document why your plan cannot enforce it — same honesty standard as D01).
5. Capture evidence: PR URL, failed job log excerpt, protection screenshot/notes.
6. Restore the test, push, confirm green, merge or close as you prefer.

```bash
git switch main
git branch -D demo/ci-gate-failure  # after you are done; delete remote branch too
```

**Practice — reproduce:** Without looking at this section, recreate a failing PR and a fixed PR; keep both log links in your Progress Log.

**Challenge:** Introduce a flaky test (`assert random.choice([True, False])`), observe intermittent failure, then replace it with a deterministic test and document why blind retry-on-failure is dangerous in a merge gate.

**Verify:** Another engineer can see that a red required check prevents merge (or can read your documented plan limitation).

**Reflect:** Who owns fixing a red main branch within your platform’s working agreement?

### 4.3.4 Path filters vs required checks (monorepo trap)

Path filters (`paths: [app/**, …]`) save minutes in a monorepo — and create a classic Platform Engineering failure mode:

| Setup | Docs-only PR | App PR |
| --- | --- | --- |
| Required check + **no** path filter | Workflow runs (fast no-op or full tests) → check completes | Check runs |
| Required check + path filter on `app/**` only | Workflow **skipped** → required check never reports success → **merge blocked** | Check runs |

GitHub does not treat “skipped because paths did not match” as a passing required status unless you add an explicit always-pass companion job or use rulesets/path-aware required checks carefully.

**Worked example — prove the trap (optional, disposable):**

1. Add a temporary `paths:` filter that only matches `app/**`.
2. Open a PR that changes only `README.md`.
3. Observe that `harbour-validate` does not run and merge stays blocked if the check is required.
4. Revert the filter (return to Section 4.3.2) **or** introduce a deliberate pattern such as:

```yaml
# Path-aware optimisation — explicit permissions required.
# dorny/paths-filter uses the GitHub pull-request API for PR events;
# without pull-requests: read the filter step can fail even when YAML is otherwise correct.
permissions:
  contents: read
  pull-requests: read

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      app: ${{ steps.filter.outputs.app }}
    steps:
      - uses: actions/checkout@v4
      - id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            app:
              - 'app/**'
              - '.github/workflows/harbour-validate.yml'

  test:
    needs: changes
    if: needs.changes.outputs.app == 'true'
    # … same test steps as before …

  # Required check name this job if you use path filters:
  gate:
    needs: [changes, test]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Resolve required gate
        run: |
          if [ "${{ needs.changes.outputs.app }}" != "true" ]; then
            echo "No app changes — validate gate satisfied without app tests"
            exit 0
          fi
          if [ "${{ needs.test.result }}" != "success" ]; then
            echo "App tests did not succeed: ${{ needs.test.result }}"
            exit 1
          fi
```

Require the **`gate`** job (not `test`) when you adopt path filters. Keep `pull-requests: read` on any workflow that uses `dorny/paths-filter` against pull_request events (and keep `contents: read` for checkout). Until you need monorepo savings, keep the simple always-run workflow from 4.3.2.

**Practice:** Document in an ADR whether Harbour’s training repo uses always-run validation or a path-aware gate — and name the required check exactly.

**Challenge:** Explain how a second service (`services/harbour-ping/**`) should join the filter matrix without creating more skipped-check deadlocks.

---

## Section 4.4 — Treat CI as a privileged system

### 4.4.1 Threat model: hostile pull request

Assume an external contributor opens a PR that runs `curl` to exfiltrate environment variables.

| Control | Intent |
| --- | --- |
| `permissions: contents: read` on validate | Default deny writes |
| No `pull_request_target` for build/test of untrusted code | Avoid privileged checkout + secrets |
| Secrets not available to `pull_request` from forks | Prevent trivial secret theft |
| Hosted ephemeral runners for untrusted PRs | Avoid persistent self-hosted contamination |
| Separate release workflow with environment protection | Publish only from trusted refs |

**Never** put `GITHUB_TOKEN` write scopes or registry passwords on the validation workflow “so we can also push a preview image” from fork PRs.

### 4.4.2 Worked example — permission matrix

Create `docs/decisions/0004-ci-permission-matrix.md`:

```markdown
# ADR 0004 — CI permission matrix (Harbour)

| Job | Trigger | contents | packages | id-token | secrets | May publish image? |
| --- | --- | --- | --- | --- | --- | --- |
| harbour-validate / test | pull_request, push main | read | none | none | none | No |
| harbour-release / build | push main (trusted) | read | write | write (if OIDC) | registry | Yes |
| harbour-promote | workflow_dispatch / PR to deploy/ | read | read | none | none or GitOps only | No rebuild |

Untrusted fork PRs must not receive registry credentials.
```

**Practice:** In repository Settings, confirm Actions permissions are restrictive by default; note any org-level override.

**Challenge:** Sketch how OIDC to a cloud registry removes long-lived `REGISTRY_PASSWORD` (even if you still use a PAT for training).

**Verify:** Validation workflow YAML contains no `${{ secrets.` registry or deploy keys.

---

## Section 4.5 — Release once: immutable artifact + evidence

### 4.5.1 Concept: build after trust, promote the digest

After checks pass on protected `main`:

1. Build the Harbour image **once**
2. Push to a registry
3. Record **commit SHA ↔ registry manifest digest**
4. Generate SBOM / scan that digest (or the image ID you pushed)
5. Do **not** rebuild the same commit separately for “staging” and “prod”

### 4.5.2 Worked example — simple, executable release (do this first)

Ship a **single job** that tests, builds and pushes. Do not call reusable workflows yet — that refactor comes in Section 4.7 after this path works.

GHCR usually works with `GITHUB_TOKEN` and `permissions: packages: write`. Create `.github/workflows/harbour-release.yml`:

```yaml
name: harbour-release

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

concurrency:
  group: harbour-release-main
  cancel-in-progress: false

jobs:
  release:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Image name (GHCR requires lowercase owner)
        id: meta
        run: |
          OWNER_LC='${{ github.repository_owner }}'
          OWNER_LC="${OWNER_LC,,}"
          IMAGE="ghcr.io/${OWNER_LC}/harbour-api"
          echo "image=${IMAGE}" >> "$GITHUB_OUTPUT"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: app/requirements.txt

      - name: Test
        working-directory: app
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pytest -q --junitxml="${{ runner.temp }}/pytest-report.xml"

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/setup-buildx-action@v3

      - name: Build and push
        id: push
        uses: docker/build-push-action@v6
        with:
          context: app
          file: app/Dockerfile
          push: true
          tags: |
            ${{ steps.meta.outputs.image }}:${{ github.sha }}
          build-args: |
            HARBOUR_COMMIT=${{ github.sha }}

      - name: Prove digest output
        run: |
          echo "commit=${{ github.sha }}"
          echo "digest=${{ steps.push.outputs.digest }}"
          echo "ref=${{ steps.meta.outputs.image }}@${{ steps.push.outputs.digest }}"

      - name: Upload provenance note
        uses: actions/upload-artifact@v4
        with:
          name: harbour-release-${{ github.sha }}
          path: ${{ runner.temp }}/pytest-report.xml
          if-no-files-found: ignore
```

`steps.push.outputs.digest` from `build-push-action` (after a successful push) is the **registry digest** you will promote. Prefer that over guessing `RepoDigests` locally.

Push the workflow, merge to `main`, and open the run. Copy:

- commit SHA
- `digest=sha256:…`
- image reference `ghcr.io/<owner>/harbour-api@sha256:…`

**Practice — reproduce:** `docker buildx imagetools inspect` on that `@sha256:…` reference from your laptop (after `docker login ghcr.io`) and confirm the digest matches the job log.

**Challenge:** Run Trivy/Grype against that digest; write a three-line policy note: what would block release, what needs approval, what is accepted risk.

**Verify:** You can show one merge commit, one digest, one workflow run URL. Only after this works should you introduce reusable workflows (Section 4.7) or optional provenance/SBOM flags on the build.

### 4.5.3 Later enhancement — provenance and SBOM on the same push

Once 4.5.2 is green, you may extend the build-push step (same job, still no reusable-workflow dependency):

```yaml
          provenance: true
          sbom: true
```

Also tag `:main` if you want a moving label for humans — **never** promote `:main` into `deploy/`; promote the digest from the job output.

---

## Section 4.6 — Promote by digest (no rebuild)

### 4.6.1 Concept

Promotion updates **pointers** (desired state), not source. For Harbour before full GitOps (D06), keep a small desired-state file the platform will later reconcile:

`deploy/harbour-api/image-ref.txt`:

```text
# Format: repository@digest — never a mutable floating tag for promoted envs
ghcr.io/example/harbour-api@sha256:replace-me
```

Environments:

| Env | How you promote in training |
| --- | --- |
| `dev` | Auto-update on main release (optional) |
| `staging` | PR that only changes `image-ref.txt` to an existing digest |

### 4.6.2 Worked example — first pin + staging promotion PR

After a successful release, set the file to the real digest (replace owner/digest):

```bash
cd "$HARBOUR_ROOT"
mkdir -p deploy/harbour-api
cat > deploy/harbour-api/image-ref.txt <<EOF
ghcr.io/<owner-lowercase>/harbour-api@sha256:<digest-from-release-job>
EOF
printf '%s\n' '# Harbour deploy pointers' 'Promote by editing image-ref.txt to an existing digest.' > deploy/harbour-api/README.md
git add deploy/harbour-api
git commit -m "deploy: pin Harbour API to release digest"
git push
```

Simulate rollback inventory — keep the previous digest in your Progress Log or:

```bash
echo "previous=ghcr.io/...@sha256:old" >> docs/releases/promotion-log.md
echo "current=ghcr.io/...@sha256:new" >> docs/releases/promotion-log.md
```

**Promotion PR demo:** change *only* `image-ref.txt` to a known-good older digest on a branch, open PR titled `promote(staging): roll back harbour-api to <short-sha>`, merge after review. No Docker build in that PR.

### 4.6.3 Worked example — promotion guard script (with tests)

Inline one-liners in workflows are easy to get wrong. This broken pattern looks clever and fails on the example file:

```bash
# BROKEN — do not use
# tr removes newlines first, so the comment and reference become one line;
# sed '/^#/d' then deletes everything and REF is empty.
REF="$(tr -d '[:space:]' < deploy/harbour-api/image-ref.txt | sed '/^#/d' | tail -n 1)"
```

**Fix:** strip comments and blanks **first**, require **exactly one** remaining reference (reject multiple pins so the deploy contract is unambiguous), then validate the full digest form.

Create `deploy/harbour-api/check-image-ref.sh`:

```bash
#!/usr/bin/env bash
# Usage: check-image-ref.sh <image-ref-file>
set -euo pipefail

FILE="${1:?usage: check-image-ref.sh <file>}"
if [[ ! -f "$FILE" ]]; then
  echo "error: file not found: $FILE" >&2
  exit 2
fi

# Drop comment lines and blanks; collect remaining reference lines.
mapfile -t REFS < <(
  sed -e 's/[[:space:]]*$//' -e 's/^[[:space:]]*//' "$FILE" \
    | grep -v '^#' \
    | grep -v '^$' || true
)

if [[ ${#REFS[@]} -eq 0 ]]; then
  echo "error: no image reference found in $FILE" >&2
  exit 1
fi

if [[ ${#REFS[@]} -gt 1 ]]; then
  echo "error: expected exactly one image reference in $FILE, found ${#REFS[@]}:" >&2
  printf '  %s\n' "${REFS[@]}" >&2
  exit 1
fi

REF="${REFS[0]}"
echo "ref=${REF}"

# Require registry/name@sha256:<64 hex>
if [[ "$REF" =~ ^[a-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]; then
  echo "OK: digest pin"
  exit 0
fi

echo "error: refuse promotion ref (need name@sha256:<64-hex>): ${REF}" >&2
exit 1
```

```bash
chmod +x deploy/harbour-api/check-image-ref.sh
```

**Worked example — run it locally on good and bad files:**

```bash
cd "$HARBOUR_ROOT"

# Good (comment + digest)
cat > /tmp/harbour-ref-good.txt <<'EOF'
# Format: repository@digest
ghcr.io/example/harbour-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
EOF
./deploy/harbour-api/check-image-ref.sh /tmp/harbour-ref-good.txt

# Bad: mutable tag
echo 'ghcr.io/example/harbour-api:latest' > /tmp/harbour-ref-tag.txt
./deploy/harbour-api/check-image-ref.sh /tmp/harbour-ref-tag.txt && echo "UNEXPECTED SUCCESS" || echo "rejected as expected"

# Bad: truncated digest
echo 'ghcr.io/example/harbour-api@sha256:abcd' > /tmp/harbour-ref-short.txt
./deploy/harbour-api/check-image-ref.sh /tmp/harbour-ref-short.txt && echo "UNEXPECTED SUCCESS" || echo "rejected as expected"

# Bad: multiple references (ambiguous deploy contract)
cat > /tmp/harbour-ref-multi.txt <<'EOF'
ghcr.io/example/harbour-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ghcr.io/example/harbour-api@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
EOF
./deploy/harbour-api/check-image-ref.sh /tmp/harbour-ref-multi.txt && echo "UNEXPECTED SUCCESS" || echo "rejected as expected"
```

**Automated tests for the policy script** — delivery guards deserve CI of their own. Create `deploy/harbour-api/test_check_image_ref.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CHECK="$ROOT/check-image-ref.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

# comment + valid digest must succeed
cat > "$TMP/good.txt" <<'EOF'
# comment
ghcr.io/example/harbour-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
EOF
"$CHECK" "$TMP/good.txt" >/dev/null || fail "good digest"
pass "good digest"

# mutable tag must fail
echo 'ghcr.io/example/harbour-api:latest' > "$TMP/tag.txt"
"$CHECK" "$TMP/tag.txt" >/dev/null 2>&1 && fail "tag should be rejected" || pass "tag rejected"

# short digest must fail
echo 'ghcr.io/example/harbour-api@sha256:abcd' > "$TMP/short.txt"
"$CHECK" "$TMP/short.txt" >/dev/null 2>&1 && fail "short digest should be rejected" || pass "short digest rejected"

# comment-only must fail
echo '# only a comment' > "$TMP/empty.txt"
"$CHECK" "$TMP/empty.txt" >/dev/null 2>&1 && fail "comment-only should be rejected" || pass "comment-only rejected"

# multiple references must fail (do not silently take the first)
cat > "$TMP/multi.txt" <<'EOF'
ghcr.io/example/harbour-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ghcr.io/example/harbour-api@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
EOF
"$CHECK" "$TMP/multi.txt" >/dev/null 2>&1 && fail "multiple refs should be rejected" || pass "multiple refs rejected"

pass "all check-image-ref tests"
```

```bash
chmod +x deploy/harbour-api/test_check_image_ref.sh
./deploy/harbour-api/test_check_image_ref.sh
```

Wire the same script into CI — `.github/workflows/harbour-promote-guard.yml`:

```yaml
name: harbour-promote-guard

on:
  pull_request:
    paths:
      - "deploy/harbour-api/**"
      - ".github/workflows/harbour-promote-guard.yml"

permissions:
  contents: read

jobs:
  digest-only:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit-test the promotion policy script
        run: ./deploy/harbour-api/test_check_image_ref.sh
      - name: Validate image-ref.txt
        run: ./deploy/harbour-api/check-image-ref.sh deploy/harbour-api/image-ref.txt
```

If this workflow is a **required** check, remember Section 4.3.4: path filters can skip it on unrelated PRs. Either keep it non-required, always-run the script tests on every PR, or use an explicit resolving `gate` job.

**Practice — reproduce:** Create a PR that tries to promote `.../harbour-api:latest` and show the guard failing; fix to a full `@sha256:` + 64 hex and show success.

**Challenge:** Extend the regex to allow optional registry ports or digests recorded as `name:tag@sha256:…` (OCI) — only if you add tests first.

**Verify:** Staging pointer equals a digest that exists in the registry; rolling back is another pointer change, not a rebuild; `test_check_image_ref.sh` is green.

---

## Section 4.7 — Reusable pipeline for a second service

### 4.7.1 Worked example — tiny second service

Create `services/harbour-ping/app.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "harbour-ping"}
```

`services/harbour-ping/requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
pytest==8.3.4
```

`services/harbour-ping/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["service"] == "harbour-ping"
```

### 4.7.2 Worked example — reusable callable workflow (correct wiring)

GitHub treats `workflow_call` inputs as belonging to **callable** runs. Do not mix “optional input or default” tricks on the same job that also handles `pull_request` without a clear split. Use a **reusable** workflow plus thin callers.

**1. Reusable file** — `.github/workflows/python-validate.yml`:

```yaml
name: python-validate

on:
  workflow_call:
    inputs:
      working-directory:
        required: true
        type: string
      requirements-file:
        required: false
        type: string
        default: requirements.txt

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: ${{ inputs.working-directory }}/${{ inputs.requirements-file }}
      - name: Install and test
        run: |
          python -m pip install --upgrade pip
          pip install -r "${{ inputs.requirements-file }}"
          pytest -q --junitxml="${{ runner.temp }}/pytest-report.xml"
      - name: Fail if the tree was dirtied
        working-directory: ${{ github.workspace }}
        run: |
          if [ -n "$(git status --porcelain)" ]; then
            git status --porcelain
            exit 1
          fi
```

**2. Caller for Harbour API** — replace the inline job body of `harbour-validate.yml` (keep **no path filters** until you add a resolving gate from 4.3.4):

```yaml
name: harbour-validate

on:
  pull_request:
  push:
    branches: ["main"]

permissions:
  contents: read

jobs:
  test:
    uses: ./.github/workflows/python-validate.yml
    with:
      working-directory: app
```

**3. Caller for harbour-ping** — `.github/workflows/harbour-ping-validate.yml` (same always-run rule, or a dedicated gate if you later add path filters):

```yaml
name: harbour-ping-validate

on:
  pull_request:
  push:
    branches: ["main"]

permissions:
  contents: read

jobs:
  test:
    uses: ./.github/workflows/python-validate.yml
    with:
      working-directory: services/harbour-ping
```

**4. Optional refactor of release** — only after Section 4.5.2 has published a digest successfully, you may add a `workflow_call` entry point or `needs:` a callable validate job. Do not invent that wiring until the simple release path is proven.

Document ownership and breaking-change policy in `docs/decisions/0004-reusable-validate.md` (who may change `python-validate.yml`, how consumers are notified).

**Practice — reproduce:** Make ping fail a test on a PR and show `harbour-ping-validate` goes red while Harbour API stays green if you temporarily use path filters *with* a resolving gate (4.3.4); otherwise both callers may still run.

**Challenge:** Add a third caller with a different requirements filename via `requirements-file` input.

**Verify:** Two services share one policy (pinned installs, `contents: read`, reports outside the checkout); changing the reusable workflow affects both callers by design.

---

## Section 4.8 — Failure injection and diagnosis

### 4.8.1 Worked example — classify failures

Cause each once (disposable branches), capture logs, fill the table:

| Fault you inject | How | Likely symptoms | Remediation |
| --- | --- | --- | --- |
| Code/test regression | `assert False` in unit test | Red validate, clear traceback | Fix test/code |
| Dependency install failure | Typo in package name in requirements | Pip error early in job | Fix pin; do not retry forever |
| Cache weirdness | Corrupt by changing requirement unexpectedly | Inconsistent local vs CI | Clear caches; make install deterministic |
| Registry auth failure | Wrong token on release | Push denied | Fix identity; ensure PR jobs lack this secret |
| Bad promotion | Tag without digest | Guard job fails | Pin `@sha256:` |

**Practice — reproduce:** Pick two rows, inject, diagnose from logs only (pretend you did not cause them), write a short failure report.

**Challenge:** Disable a runner label or break `working-directory` and show how the failure differs from an application bug.

---

## Practical Assessment — Chapter 4 — trusted software supply chain

**Scenario:** Your platform offers delivery to two application teams. One ships a legitimate Harbour change; another submits untrusted or failing work. Show useful feedback without granting publish rights.

Align with [D04 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) and the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D04 acceptance criterion.

### Required deliverables

1. **PR pipeline** with pinned dependency installs, automated checks, and evidence that a failing check blocks merge (or an honest plan limitation).
2. **Trusted release** publishing an image with commit SHA, **registry digest**, and SBOM/scan notes for that digest.
3. **Permission model** proving validate jobs cannot publish; release uses narrow write permissions.
4. **Promotion** of the **same** digest into `deploy/` (or equivalent), plus a rollback to a previous digest without rebuilding.
5. **Reusable validate path** exercised by Harbour API and harbour-ping (or a second service).
6. **Failure report** covering at least two fault classes from Section 4.8.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| PR validation | Workflow exists | Deterministic installs, required check, useful artifacts | Flake policy, concurrency, path filters |
| Trust boundaries | Single mega-workflow | Clear validate vs release vs promote | OIDC, environment protection, fork PR hard rules |
| Artifacts | Tag-only publish | Digest recorded with commit + run URL | Provenance/SBOM/signing with known limits |
| Promotion | Rebuild per env | Same digest pinned; rollback demonstrated | GitOps-ready desired state only |
| Reuse | Copy-paste YAML | Second service shares pattern/template | Versioned reusable workflow + change policy |
| Diagnosis | “Re-run until green” | Classifies fault with log evidence | Prevents recurrence in platform defaults |

**Completion standard:** **Competent** on every row.

### Self-check

- Can a stranger explain what commit produced which digest from your links alone?
- Does a red required check block merge?
- Can an untrusted PR steal a registry secret from your YAML/settings design?
- Does promotion reject `:latest`?
- Did learning Complete (Progress Log) and Final Project Checklist acceptance stay separate if integration lags?

### Example assessment conclusion (evidence still required)

> harbour-validate is required on `main` and runs on every PR (path-aware gates documented separately). A deliberate failing PR stayed unmergeable. harbour-release (single job) publishes `ghcr.io/…/harbour-api@sha256:…` for commit `abc123`. `check-image-ref.sh` rejects `:latest` and accepts a 64-hex digest; its shell tests are green. `deploy/harbour-api/image-ref.txt` pins that digest; a rollback PR pointed at the previous digest without rebuilding. harbour-ping calls the reusable validate workflow. Validate jobs have `contents: read` only.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Gate merges | Always-run required check first | Path filters without a resolving gate |
| Keep clean-tree checks honest | Write reports under `${{ runner.temp }}` | JUnit XML inside the checkout |
| Trust an image | Registry digest + commit SHA + run URL | `:latest` or rebuild-per-env |
| Handle fork PRs | read-only validate, no secrets | `pull_request_target` + build untrusted code |
| Promote | Script + tests; exactly one `@sha256:` + 64 hex | `tr`-then-`sed`; `:latest`; multiple refs in one file |
| Path-aware PR filters | `permissions: pull-requests: read` (+ contents) | Relying on default token scopes for `paths-filter` |
| Debug CI | Classify fault with logs | Infinite re-run |
| Reuse | Working simple pipeline, then callable workflow | Reusable `workflow_call` before anything publishes |

## Glossary

| Term | Definition |
| --- | --- |
| Required check | Branch rule that blocks merge until named CI jobs succeed |
| Immutable artifact | Bytes that do not change; identified by digest |
| Promotion | Moving a known artifact to an environment pointer |
| Provenance | Metadata linking artifact to source and build |
| OIDC federation | Short-lived cloud creds from the CI identity provider |
| Reusable workflow | Callable CI definition shared by multiple consumers |
| Untrusted PR | Code that must not receive privileged secrets |
| Merge gate | Policy combination of reviews + required checks |

## References

- [GitHub Actions — Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [GitHub — Using reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Docker build-push-action](https://github.com/docker/build-push-action)
- [SLSA](https://slsa.dev/)
- [GitLab CI/CD security](https://docs.gitlab.com/ci/security/)
- [OpenID Connect — GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

**Previous chapter:** [Chapter 3 — Docker and Containerization](D03%20Docker%20and%20Containerization.md) · **Course detail:** [D04 — CI/CD and Build Automation](../../3%20Course%20Detail/3.1%20DevOps/D04%20CICD%20and%20Build%20Automation.md) · **Next chapter:** Chapter 5 — Infrastructure as Code and Terraform (not yet authored) · **Checklist:** [Final Project Checklist · D04](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)

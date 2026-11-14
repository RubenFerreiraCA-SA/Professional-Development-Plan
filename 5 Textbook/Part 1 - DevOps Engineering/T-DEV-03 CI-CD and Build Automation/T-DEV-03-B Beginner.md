# T-DEV-03-B — Beginner Foundations

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-b"></a>
#### T-DEV-03-B — Beginner Foundations

**The problem.** Without automation, builds happen on someone's laptop, tests run when remembered, and nobody can say what is in production. A *pipeline* runs the same steps for every change on a clean machine and reports the result where reviewers can see it.

**Vocabulary**

| Term | Meaning |
| --- | --- |
| CI (continuous integration) | Automatically build and test every change as it is proposed or merged. |
| CD (continuous delivery/deployment) | Automatically prepare (delivery) or release (deployment) verified changes. |
| Pipeline / workflow | A defined sequence of automated jobs triggered by events. |
| Runner | The machine that executes a job. |
| Artifact | A build output, such as a container image or package. |
| Required check | A job that must pass before a change can merge. |

**A first pipeline.** A pull-request validation workflow in GitHub Actions syntax:

```yaml
name: validate
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
```

Read it top to bottom: *when* it runs (`on`), what it may do (`permissions`), where (`runs-on`), and the steps. Notice it can only read the repository; it cannot publish anything.

**Make the code testable first.** CI cannot test what has no tests. A tiny example for a service with a health endpoint:

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_ok():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
```

Run the test locally before wiring it into CI. Then break it on a branch, open a pull request and watch the failing check appear. A red check that blocks the merge is the whole point.

**Rules of thumb**

1. Install from pinned dependencies so today's build matches yesterday's.
2. Run in a clean environment, never on a developer's machine.
3. Keep fast tests on every pull request; run slower suites later.
4. A failing required check blocks merge; do not "retry until green".
5. Never give a validation job credentials to publish.

**Exercise.** Add the workflow above to a practice repository, mark the `test` job as a required check, introduce a failing test on a branch and confirm the merge button is blocked.

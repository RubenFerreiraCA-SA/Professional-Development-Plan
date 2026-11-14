# T-DEV-03-P — Professional Engineering

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-p"></a>
#### T-DEV-03-P — Professional Engineering

**Treat CI as a privileged system.** A pipeline holds credentials and can change production. Assume a hostile pull request tries to exfiltrate environment variables:

| Control | Intent |
| --- | --- |
| `permissions: contents: read` on validation | Default deny for writes |
| No `pull_request_target` combined with checkout of untrusted code | Avoid privileged context plus attacker-controlled code |
| Secrets not exposed to fork pull requests | Prevent trivial theft |
| Ephemeral hosted runners for untrusted code | Avoid persistent self-hosted contamination |
| Separate release workflow with environment protection | Publish only from trusted refs |
| Pin third-party actions by commit SHA | Reduce action-supply-chain risk |

Never add write scopes or registry passwords to the validation workflow so it can "also push a preview image" from forks. Keep a permission matrix (workflow × token scope × secrets × triggers) in the repository.

**Short-lived cloud credentials with OpenID Connect.** Rather than storing long-lived keys, the CI provider issues a signed identity token per run, and the cloud exchanges it for temporary credentials. Constrain the trust relationship to the specific repository, branch or environment (`sub` claim) and audience, not a wildcard:

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::<account>:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:example-org/orders:environment:release"
    }
  }
}
```

**A trusted release workflow.** Build once, push, capture the digest and write evidence:

```yaml
on:
  push:
    branches: [main]
permissions:
  contents: read
  id-token: write      # for OIDC
  packages: write
jobs:
  release:
    runs-on: ubuntu-24.04
    environment: release
    steps:
      - uses: actions/checkout@v4
      - id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/example-org/orders-api:${{ github.sha }}
          provenance: true
          sbom: true
      - run: echo "${{ github.sha }} ${{ steps.build.outputs.digest }}" >> release-evidence.txt
```

Record, for every release: commit SHA, registry digest, workflow run URL and scan or SBOM output for *that digest*.

**Promotion guard with tests.** Because promotion is a text change, validate it like code. A small script that extracts exactly one reference, rejects mutable tags and multiple references, and can be unit-tested in CI turns a policy into an automatic check. Roll back by promoting a previous known digest; no rebuild is needed.

**Reusable pipelines.** Once a simple pipeline works, extract the common steps into a callable workflow (`workflow_call`) or shared template so a second service reuses them rather than copy-pasting. Version the shared workflow and define a change policy: pinned versions for consumers, a deprecation note for breaking changes, and tests for the template itself.

**Merge gate design.** Combine reviews with required checks. Required checks should include validation, policy and promotion verification (a job that always reports). If the plan cannot enforce the gate, document the gap and the compensating control.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Gate merges | An always-running required check | Path filters without a resolving gate |
| Trust an image | Registry digest plus commit plus run URL | `:latest` or rebuild per environment |
| Handle fork PRs | Read-only validation, no secrets | `pull_request_target` with untrusted checkout |
| Promote | A script with tests: one `@sha256:` reference | Tag-only references |
| Authenticate to a cloud | OIDC with a narrow `sub` and `aud` | Stored long-lived access keys |
| Debug CI | Classify the fault using logs | Re-running until green |
| Reuse | A working simple pipeline, then a callable workflow | Abstracting before anything works |

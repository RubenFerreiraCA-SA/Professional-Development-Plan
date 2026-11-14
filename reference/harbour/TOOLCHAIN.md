# Harbour teaching toolchain matrix

Pin these versions for labs and CI. Do **not** float `latest`.

| Component | Version | Notes |
| --- | ---: | --- |
| Kubernetes (kind node image / cluster) | **1.31.x** | Match `kubectl` minor |
| kubectl | **v1.31.0** | CI: `azure/setup-kubectl@v4` |
| Kyverno CLI | **1.13.4** | Checksum in `policy.yml` |
| Kyverno Helm chart | **3.3.4** | App version aligns with CLI 1.13.4 |
| GitHub CLI (`gh`) | **2.102.0** | Attestation fixes; checksum in `promotion-verify.yml` |
| Flux | version recorded in learner ADR | Keep consistent within a clean-room run |
| Helm | 3.x | Required for Kyverno install |

## Install Kyverno (pinned)

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm upgrade --install kyverno kyverno/kyverno \
  -n kyverno --create-namespace \
  --version 3.3.4
kubectl -n kyverno rollout status deploy --timeout=180s
```

## Resolve pullable digests (M-01)

```bash
export HARBOUR_PULLABLE_DIGEST_IMG="$(
  docker buildx imagetools inspect nginx:1.27-alpine --format '{{.Manifest.Digest}}' \
  | awk '{print "nginx@"$0}'
)"
export HARBOUR_PULLABLE_DBG_IMG="$(
  docker buildx imagetools inspect busybox:1.36 --format '{{.Manifest.Digest}}' \
  | awk '{print "busybox@"$0}'
)"
# Optional: validate pull before admission lab
docker pull "$HARBOUR_PULLABLE_DIGEST_IMG"
platform/bin/harbour-policy-admit "${SVC}-staging"
```

## Checksums (frozen at authoring)

| Artifact | SHA256 |
| --- | --- |
| `kyverno-cli_v1.13.4_linux_x86_64.tar.gz` | `abd318dbb971ab6de2bbe3b7226f4a03230d5c9c651df8a29b6b5e085a55aeeb` |
| `gh_2.102.0_linux_amd64.tar.gz` | `bb766f710eef8ede859c18578c72c327597cd4c8a85b06001b1f3843c6019386` |

Re-verify checksums against upstream release assets before changing pins.

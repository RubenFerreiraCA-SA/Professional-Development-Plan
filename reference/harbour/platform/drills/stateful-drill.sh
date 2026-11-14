#!/usr/bin/env bash
# Canonical Harbour stateful drill (G1-04). P04 must link here — not a shortened outline.
# Phases: seed | backup | write-after | kill-db | destroy | restore
# Injection: HARBOUR_RESTORE_FAIL_AFTER=suspend|copy|pg_restore (unknown values rejected)
set -euo pipefail
NS="${1:?namespace}"; PHASE="${2:?phase}"; SVC="${SVC:?set SVC}"
BIN="$(cd "$(dirname "$0")/../bin" && pwd)"
export PYTHONPATH="${BIN}${PYTHONPATH:+:$PYTHONPATH}"

if [ -n "${HARBOUR_DRILL_OUT:-}" ]; then
  OUT="$HARBOUR_DRILL_OUT"
elif [ "${HARBOUR_DRILL_NEW:-0}" != "1" ] && [ -f /tmp/harbour-stateful-out.path ]; then
  OUT="$(cat /tmp/harbour-stateful-out.path)"
else
  RUN_ID="${HARBOUR_DRILL_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
  OUT="docs/final/drills/stateful-$RUN_ID"
fi
mkdir -p "$OUT" ~/harbour-backups
echo "$OUT" > /tmp/harbour-stateful-out.path
export HARBOUR_DRILL_OUT="$OUT"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$OUT/timeline.log"; }

wait_until() {
  local deadline=$(( $(date +%s) + $1 )); shift; local desc="$1"; shift
  [ "$1" = "--" ] && shift
  until "$@"; do
    [ $(date +%s) -ge "$deadline" ] && { log "TIMEOUT waiting for: $desc"; return 1; }
    sleep 2
  done
}

PF_PID=""; MAINT=0; DB_UNSAFE=0
app_stop_pf() { [ -n "${PF_PID:-}" ] && kill "$PF_PID" 2>/dev/null || true; PF_PID=""; }
app_pf() {
  app_stop_pf
  kubectl -n "$NS" port-forward "svc/$SVC" 18080:80 >/tmp/pf-ledger.log 2>&1 & PF_PID=$!
  wait_until 30 "port-forward HTTP health" -- bash -c '
    r=$(curl -sS --max-time 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health || true)
    [[ "$r" =~ ^[0-9]+$ ]]
  '
}
cleanup_on_exit() {
  if [ "${MAINT:-0}" = "1" ]; then
    if [ "${DB_UNSAFE:-0}" = "1" ]; then
      log "cleanup: DB_UNSAFE=1 — leaving Flux suspended; operator must verify DB"
      echo "REQUIRES_OPERATOR db_unsafe $(date -u +%FT%TZ)" | tee -a "$OUT/maintenance-cleanup.txt"
      kubectl -n "$NS" annotate kustomization "$SVC" \
        harbour.example/maintenance=operator-required --overwrite || true
    else
      log "cleanup: safe resume after pre-restore failure"
      flux resume kustomization "$SVC" -n "$NS" || log "cleanup: flux resume failed"
      kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance- --overwrite || true
      flux reconcile kustomization "$SVC" -n "$NS" --with-source || true
      echo "trap-safe-resume $(date -u +%FT%TZ)" >> "$OUT/maintenance-cleanup.txt"
    fi
  fi
  app_stop_pf
}
trap cleanup_on_exit EXIT

http() { curl -sf --max-time 5 -H 'content-type: application/json' "$@"; }
app_json() { http http://127.0.0.1:18080/v1/entries; }
app_count() { app_json | python3 -c 'import sys,json; print(json.load(sys.stdin)["count"])'; }
notes_include() {
  local want="$1"
  app_json | WANT="$want" python3 -c 'import os,sys,json; notes={e["note"] for e in json.load(sys.stdin)["entries"]}; sys.exit(0 if os.environ["WANT"] in notes else 1)'
}

case "$PHASE" in
  seed)
    app_pf
    wait_until 60 "ready query_ok" -- bash -c 'curl -sf http://127.0.0.1:18080/ready | grep -q query_ok'
    for i in $(seq 1 20); do http -d "{\"note\":\"A-$i\"}" http://127.0.0.1:18080/v1/entries >/dev/null; done
    log "seeded via HTTP count=$(app_count)"
    app_stop_pf ;;
  backup)
    J="manual-backup-$(date +%s)"
    kubectl -n "$NS" create job --from=cronjob/postgres-backup "$J"
    kubectl -n "$NS" wait --for=condition=complete "job/$J" --timeout=120s
    date -u +%FT%TZ > "$OUT/backup_completed_at.txt"
    # Helper mount + off-cluster copy (digest resolved at setup — see TOOLCHAIN.md)
    PG_IMG="${HARBOUR_POSTGRES_IMAGE:?set HARBOUR_POSTGRES_IMAGE to postgres@sha256:...}"
    kubectl -n "$NS" delete pod backup-helper --ignore-not-found --wait=true
    kubectl -n "$NS" run backup-helper --restart=Never --image="$PG_IMG" \
      --overrides="{\"spec\":{\"securityContext\":{\"runAsNonRoot\":true,\"runAsUser\":70,\"runAsGroup\":70,\"fsGroup\":70,\"seccompProfile\":{\"type\":\"RuntimeDefault\"}},\"containers\":[{\"name\":\"backup-helper\",\"image\":\"$PG_IMG\",\"command\":[\"sleep\",\"3600\"],\"securityContext\":{\"allowPrivilegeEscalation\":false,\"capabilities\":{\"drop\":[\"ALL\"]}},\"resources\":{\"requests\":{\"cpu\":\"10m\",\"memory\":\"32Mi\"},\"limits\":{\"memory\":\"64Mi\"}},\"volumeMounts\":[{\"name\":\"backup\",\"mountPath\":\"/backup\"}]}],\"volumes\":[{\"name\":\"backup\",\"persistentVolumeClaim\":{\"claimName\":\"postgres-backup\"}}]}}"
    kubectl -n "$NS" wait --for=condition=Ready pod/backup-helper --timeout=60s
    DUMP="$(kubectl -n "$NS" exec backup-helper -- sh -c 'ls -1t /backup/*.dump | head -1')"
    [ -n "$DUMP" ] || { log "no dump on backup PVC"; exit 1; }
    SUM_IN="$(kubectl -n "$NS" exec backup-helper -- sha256sum "$DUMP" | awk '{print $1}')"
    DEST="$HOME/harbour-backups/$(basename "$DUMP")"
    kubectl -n "$NS" cp "backup-helper:$DUMP" "$DEST"
    SUM_OUT="$(sha256sum "$DEST" | awk '{print $1}')"
    [ "$SUM_IN" = "$SUM_OUT" ] || { log "checksum mismatch"; exit 1; }
    echo "$SUM_OUT" > "$OUT/backup.sha256"
    echo "$DEST" > "$OUT/offcluster-backup.path"
    kubectl -n "$NS" delete pod backup-helper --wait=false
    app_pf
    wait_until 60 "ready query_ok" -- bash -c 'curl -sf http://127.0.0.1:18080/ready | grep -q query_ok'
    app_json > "$OUT/entries-at-backup.json"
    log "backup complete; offcluster=$(cat "$OUT/offcluster-backup.path")"
    app_stop_pf ;;
  write-after)
    app_pf
    for i in $(seq 1 5); do
      RESP="$(http -d "{\"note\":\"B-$i\"}" http://127.0.0.1:18080/v1/entries)"
      echo "$RESP" | tee -a "$OUT/ack-after-backup.jsonl"
      echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["created_at"])' \
        >> "$OUT/ack_timestamps_after_backup.txt"
    done
    date -u +%FT%TZ > "$OUT/incident_before.txt"
    app_stop_pf ;;
  kill-db)
    app_pf
    T0=$(date +%s); kubectl -n "$NS" delete pod postgres-0 --wait=false
    wait_until 90 "HTTP 503 readiness" -- bash -c '
      r=$(curl -sS --max-time 5 -o /tmp/body -w "%{http_code}" http://127.0.0.1:18080/ready || echo TRANSPORT)
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      [ "$r" = "503" ]
    '
    kubectl -n "$NS" wait --for=condition=ready pod/postgres-0 --timeout=180s
    wait_until 180 "ready query_ok after S2" -- bash -c '
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      curl -sf http://127.0.0.1:18080/ready | grep -q query_ok
    '
    log "S2 recovered RTO=$(( $(date +%s) - T0 ))s"
    app_stop_pf ;;
  destroy)
    date -u +%FT%TZ > "$OUT/incident_at.txt"
    kubectl -n "$NS" exec postgres-0 -- psql -U harbour -d harbour -c \
      "DELETE FROM ledger_entries WHERE note LIKE 'A-%' AND id % 2 = 0"
    app_pf; log "S3 damaged; http_count=$(app_count)"; app_stop_pf ;;
  restore)
    T0=$(date +%s)
    BACKUP="$(cat "$OUT/offcluster-backup.path")"
    [ -f "$BACKUP" ] || { log "missing off-cluster backup"; exit 1; }
    [ -f "$OUT/backup.sha256" ] || { log "missing backup.sha256"; exit 1; }
    [ "$(sha256sum "$BACKUP" | awk '{print $1}')" = "$(cat "$OUT/backup.sha256")" ] \
      || { log "selected backup checksum changed since copy — abort before DB modify"; exit 1; }

    case "${HARBOUR_RESTORE_FAIL_AFTER:-}" in
      ""|suspend|copy|pg_restore) ;;
      *) log "FAIL: unknown HARBOUR_RESTORE_FAIL_AFTER=${HARBOUR_RESTORE_FAIL_AFTER}"; exit 2 ;;
    esac

    DESIRED="$(kubectl -n "$NS" get deploy "$SVC" -o jsonpath='{.spec.replicas}')"
    echo "${DESIRED:-2}" > "$OUT/desired-replicas.txt"
    MAINT=1
    DB_UNSAFE=0
    flux suspend kustomization "$SVC" -n "$NS"
    kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance=restore --overwrite
    kubectl -n "$NS" scale deploy/"$SVC" --replicas=0
    kubectl -n "$NS" wait --for=delete pod -l "app=$SVC" --timeout=120s
    flux get kustomization "$SVC" -n "$NS" | tee -a "$OUT/maintenance-flux.txt" | grep -qi Suspended \
      || { log "FAIL: Flux Kustomization not Suspended"; exit 1; }
    case "${HARBOUR_RESTORE_FAIL_AFTER:-}" in
      suspend) log "injected failure after suspend (DB unchanged → safe resume)"; exit 42 ;;
    esac

    kubectl -n "$NS" cp "$BACKUP" "postgres-0:/tmp/restore.dump"
    case "${HARBOUR_RESTORE_FAIL_AFTER:-}" in
      copy) log "injected failure after backup copy (DB unchanged → safe resume)"; exit 42 ;;
    esac

    DB_UNSAFE=1
    kubectl -n "$NS" exec postgres-0 -- \
      pg_restore -U harbour -d harbour --clean --if-exists /tmp/restore.dump
    case "${HARBOUR_RESTORE_FAIL_AFTER:-}" in
      pg_restore) log "injected failure after pg_restore (DB_UNSAFE → operator required)"; exit 42 ;;
    esac

    # H-01: equivalence BEFORE clearing unsafe / resuming writers
    NS="$NS" OUT="$OUT" "$BIN/../drills/restore-verify-before-resume.sh"

    DB_UNSAFE=0
    flux resume kustomization "$SVC" -n "$NS"
    kubectl -n "$NS" annotate kustomization "$SVC" harbour.example/maintenance- --overwrite
    MAINT=0
    flux reconcile kustomization "$SVC" -n "$NS" --with-source
    kubectl -n "$NS" rollout status deploy/"$SVC" --timeout=180s
    app_pf
    wait_until 180 "ready query_ok after restore" -- bash -c '
      kill -0 '"$PF_PID"' 2>/dev/null || exit 1
      curl -sf http://127.0.0.1:18080/ready | grep -q query_ok
    '
    if notes_include B-1; then log "unexpected post-backup note B-1 still present"; exit 1; fi
    log "S3 restore service-RTO=$(( $(date +%s) - T0 ))s"
    app_stop_pf ;;
  *) echo "phases: seed backup write-after kill-db destroy restore" >&2; exit 2 ;;
esac

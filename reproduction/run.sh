#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/reproduction/config.sh"

upstream_url="https://github.com/pengzhang91/Feige.git"
upstream_commit="98ab466e74280ae9d40622c19dc7f24f01b60864"
upstream_tree="4406b0e9177f06cf24be645e8c54637137f0ab3e"
started_epoch="$(date +%s)"
work_dir="$(mktemp -d)"
formal_dir="$work_dir/Feige"
trap 'rm -rf "$work_dir"' EXIT

metric() {
  printf 'ORX_METRIC %s=%s\n' "$1" "$2"
}

timed() {
  local label="$1"
  shift
  local before after status
  before="$(date +%s)"
  set +e
  "$@"
  status=$?
  set -e
  after="$(date +%s)"
  metric "${label}_seconds" "$((after - before))"
  metric "${label}_status" "$status"
  return "$status"
}

echo "=== REPRODUCTION_CONFIG ==="
printf 'mode=%s\nseed=%s\ntrials=%s\nsim_ns=%s\n' "$MODE" "$SEED" "$TRIALS" "$SIM_NS"
printf 'upstream=%s\ncommit=%s\ntree=%s\n' "$upstream_url" "$upstream_commit" "$upstream_tree"
printf 'run_started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'kernel=%s\n' "$(uname -a)"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,uuid --format=csv,noheader
fi

if ! command -v curl >/dev/null 2>&1 || ! command -v zstd >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends ca-certificates curl zstd
fi

timed clone_seconds git clone --filter=blob:none "$upstream_url" "$formal_dir"
git -C "$formal_dir" checkout --detach "$upstream_commit"
observed_commit="$(git -C "$formal_dir" rev-parse HEAD)"
observed_tree="$(git -C "$formal_dir" rev-parse HEAD^{tree})"
test "$observed_commit" = "$upstream_commit"
test "$observed_tree" = "$upstream_tree"
metric provenance_verified 1

scan_log="$work_dir/source_scan.log"
set +e
grep -R -nE --include='*.lean' \
  '(^|[^[:alnum:]_])(sorry|admit|sorryAx)([^[:alnum:]_]|$)|^[[:space:]]*axiom[[:space:]]' \
  "$formal_dir" >"$scan_log"
scan_status=$?
set -e
if [ "$scan_status" -eq 0 ]; then
  echo "Forbidden proof-hole or project axiom tokens found:"
  cat "$scan_log"
  exit 1
elif [ "$scan_status" -ne 1 ]; then
  echo "Source scan itself failed with status $scan_status"
  exit "$scan_status"
fi
metric forbidden_source_tokens 0
metric lean_source_files "$(find "$formal_dir" -type f -name '*.lean' | wc -l | tr -d ' ')"

install_lean() {
  if ! command -v elan >/dev/null 2>&1; then
    curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh |
      sh -s -- -y --default-toolchain none
  fi
  export PATH="${ELAN_HOME:-$HOME/.elan}/bin:$PATH"
  cd "$formal_dir"
  timed cache_get lake exe cache get
  metric lean_version "\"$(lean --version | head -1)\""
}

audit_one() {
  local name="$1"
  local file="$2"
  local log="$work_dir/audit_${name}.log"
  timed "audit_${name}" bash -o pipefail -c "lake env lean '$file' 2>&1 | tee '$log'"
  python "$repo_root/reproduction/check_audit.py" "$log"
  metric "audit_${name}_allowed_axioms_only" 1
}

run_simulation() {
  timed sharpness_simulation python "$repo_root/reproduction/sharpness_check.py" \
    "$SEED" "$TRIALS" "$SIM_NS"
}

case "$MODE" in
  full)
    install_lean
    timed build_vlassis lake build VlassisThomas
    timed build_grunbaum lake build Grunbaum
    timed build_feige lake build Feige
    timed build_all lake build
    audit_one vlassis VlassisThomas/Audit.lean
    audit_one grunbaum Grunbaum/Audit.lean
    audit_one feige Feige/FinalAudit.lean
    run_simulation
    ;;
  vlassis)
    install_lean
    timed build_vlassis lake build VlassisThomas
    audit_one vlassis VlassisThomas/Audit.lean
    ;;
  grunbaum)
    install_lean
    timed build_grunbaum lake build Grunbaum
    audit_one grunbaum Grunbaum/Audit.lean
    ;;
  feige)
    install_lean
    timed build_feige lake build Feige
    audit_one feige Feige/FinalAudit.lean
    ;;
  combined)
    install_lean
    timed build_all lake build
    audit_one vlassis VlassisThomas/Audit.lean
    audit_one grunbaum Grunbaum/Audit.lean
    audit_one feige Feige/FinalAudit.lean
    ;;
  audit_vlassis)
    install_lean
    audit_one vlassis VlassisThomas/Audit.lean
    ;;
  audit_grunbaum)
    install_lean
    audit_one grunbaum Grunbaum/Audit.lean
    ;;
  audit_feige)
    install_lean
    audit_one feige Feige/FinalAudit.lean
    ;;
  scan)
    ;;
  simulation)
    run_simulation
    ;;
  provenance)
    ;;
  *)
    echo "Unknown MODE=$MODE"
    exit 2
    ;;
esac

elapsed="$(( $(date +%s) - started_epoch ))"
metric total_seconds "$elapsed"
echo "REPRODUCTION_RESULT {\"status\":\"passed\",\"mode\":\"$MODE\",\"commit\":\"$upstream_commit\",\"tree\":\"$upstream_tree\",\"forbidden_source_tokens\":0,\"elapsed_seconds\":$elapsed}"

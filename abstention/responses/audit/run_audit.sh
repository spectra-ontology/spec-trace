#!/usr/bin/env bash
# Rebuild transcript_audit.txt and helper_audit.txt for the twelve abstention solvers and query writers that produced
# the scored abstention responses (no model calls).
#
# final_agents_bb24e529.tsv lists the RAN3/RAN4 agents, final_agents_5cbc630c.tsv the RAN5 agents; the file name is the
# first eight characters of the coordinator session id. The transcripts are read from the session's subagents folder;
# the scratchpad path is only used to name each solver's own work folder, so the audit also runs after the scratchpad
# has been removed (the prompt text is the transcript's first user message).
#
# usage: bash run_audit.sh [OUT_DIR]   (default: this folder)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HERE}
KEY=$(git -C "$HERE" rev-parse --show-toplevel | tr / -)
declare -A SESSION=([bb24e529]=bb24e529-a09a-4010-8b7b-afd0b7eb9cd7 [5cbc630c]=5cbc630c-d2f4-4763-9aec-337622e1a3f8)
declare -A TABLE=([RAN3]=bb24e529 [RAN4]=bb24e529 [RAN5]=5cbc630c)
one=$(mktemp)
trap 'rm -f "$one"' EXIT
: > "$OUT/transcript_audit.txt"
: > "$OUT/helper_audit.txt"
for kind in abst_cypher abst_text_search abst_text_only; do
  for wg in RAN3 RAN4 RAN5; do
    short=${TABLE[$wg]}
    session=${SESSION[$short]}
    scratchpad=/tmp/claude-$(id -u)/$KEY/$session/scratchpad
    subagents=$HOME/.claude/projects/$KEY/$session/subagents
    grep -P "^$kind\t$wg\t" "$HERE/final_agents_$short.tsv" </dev/null | sort -t$'\t' -k3,3 > "$one" || true
    python3 "$HERE/audit_final_agents.py" --scratchpad "$scratchpad" --subagents "$subagents" "$one" >> "$OUT/transcript_audit.txt"
    if [ "$kind" != abst_cypher ]; then
      python3 "$HERE/audit_helpers.py" --subagents "$subagents" "$one" "$kind" >> "$OUT/helper_audit.txt"
    fi
  done
done

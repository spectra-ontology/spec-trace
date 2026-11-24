#!/bin/bash
# Codex 풀이를 한 번에 하나씩 돌린다. 각 디렉토리에는 packet.json 하나만 있다.
P=<tmp>/bb24e529-a09a-4010-8b7b-afd0b7eb9cd7/scratchpad/codex
for name in "$@"; do
  d=$P/$name
  [ -s $d/queries.jsonl ] && { echo "skip $name"; continue; }
  case $name in *sql*) tpl=$P/prompt_sql.txt;; *) tpl=$P/prompt_cypher.txt;; esac
  n=$(python3 -c "import json;print(len(json.load(open('$d/packet.json'))['items']))")
  prompt=$(sed "s/NITEMS/$n/g" $tpl)
  echo "start $name $(date -Is)"
  ~/.local/bin/codex exec --json --skip-git-repo-check --ignore-user-config -s workspace-write -C $d \
    -m gpt-6.1-sol -c model_reasoning_effort='"ultra"' "$prompt" </dev/null > $d/events.jsonl 2> $d/stderr.txt
  echo "end $name exit=$? $(date -Is) lines=$(wc -l < $d/queries.jsonl 2>/dev/null)"
done

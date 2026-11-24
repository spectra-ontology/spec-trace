"""Audit what the Claude Text-to-SQL and Text-to-Cypher writer sessions accessed.

Usage: audit_writer_sessions.py TRANSCRIPT_ROOT OUT_JSON

A writer session is a subagent transcript whose first task prompt names an
output file chain_eval/subagent_queries/RAN{n}_text2{sql|cypher}_run{X}.jsonl.
For every tool call the script extracts the paths it names (absolute paths,
and file names that a command opens relative to a directory it changed into)
and classifies each one:

  packet      the one schema packet the prompt names
  output      the output file the prompt names, or its directory
  scratch     a path under a session scratchpad that the writer created, or
              the scratchpad directory itself
  system      an interpreter path or /dev/null
  repair      the session's own repair request file (the engine errors of its
              own run) or its own repaired output file
  outside     anything else

It also records directory listings, references to another working group's
packet, and references to another run's query file. The writer is clean when
every path falls in the first four classes and no listing shows another file.
"""
import collections
import glob
import json
import os
import re
import sys

root, out_path = sys.argv[1], sys.argv[2]
OUT_RE = re.compile(r"(/\S*?chain_eval/subagent_queries/(RAN\d)_text2(sql|cypher)_run([A-J])(?:_repair\d*)?\.jsonl)")
PKT_RE = re.compile(r"(/\S*?chain_eval/subagent_packets(?:_sql)?/(RAN\d)_schema\.json)")
ABS_RE = re.compile(r"(/(?:home|tmp|usr|etc|var|opt|mnt|root|dev)[^\s'\"\)\]\}<>,;|`$]*)")
REL_OPEN_RE = re.compile(r"open\(\s*['\"]([^'\"/$][^'\"]*)['\"]")
LIST_RE = re.compile(r"(?:^|[\s;&|(])(ls|find|tree|du)\s+([^\n;&|]*)")
SCRATCH_RE = re.compile(r"^/tmp/claude-1000/[^/]+/[^/]+/scratchpad(?:/|$)")
SYSTEM = ("/usr/bin/", "/bin/", "/dev/null", "/usr/lib/")


def prompt_of(recs):
    for r in recs:
        if r.get("type") != "user":
            continue
        c = r.get("message", {}).get("content")
        t = c if isinstance(c, str) else " ".join(
            b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
        if t.strip() and not t.lstrip().startswith("<system-reminder>"):
            return t
    return ""


def tool_calls(recs):
    for r in recs:
        if r.get("type") != "assistant":
            continue
        c = r.get("message", {}).get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    yield b.get("name"), b.get("input") or {}


sessions = []
for tp in sorted(glob.glob(os.path.join(root, "*", "subagents", "*.jsonl"))):
    recs = []
    with open(tp, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    recs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    prompt = prompt_of(recs)
    mo, mp = OUT_RE.search(prompt), PKT_RE.search(prompt)
    if not (mo and mp):
        continue
    output, wg, lang, run = mo.groups()
    packet, pkt_wg = mp.groups()
    out_dir = os.path.dirname(output)
    own_repair = re.compile(
        rf"chain_eval/subagent_queries/(?:repair_requests/{wg}_text2{lang}_run{run}_round\d+|{wg}_text2{lang}_run{run}_repair\d*)\.jsonl$")
    created = set()
    classes = collections.Counter()
    outside, listings, cross = [], [], []
    n_calls = 0
    tools = collections.Counter()
    for name, inp in tool_calls(recs):
        n_calls += 1
        tools[name] += 1
        if name in ("SubagentHandback",):
            continue
        if name in ("Write", "Edit", "NotebookEdit"):
            p = inp.get("file_path", "")
            created.add(p)
            cls = "output" if p == output else "scratch" if SCRATCH_RE.match(p) else "outside"
            classes[cls] += 1
            if cls == "outside":
                outside.append({"tool": name, "path": p})
            continue
        text = "\n".join(str(v) for v in inp.values())
        if name not in ("Bash", "Read"):
            outside.append({"tool": name, "path": text[:200]})
            classes["outside"] += 1
            continue
        for m in re.finditer(r"(?:cat\s*>+\s*|>\s*|mkdir\s+-p\s+)(/tmp/[^\s'\"<>]+)", text):
            created.add(m.group(1).rstrip("/"))
        for m in re.finditer(r"open\(\s*['\"](/tmp/[^'\"]+)['\"]\s*,\s*['\"][wa]", text):
            created.add(m.group(1))
        for p in ABS_RE.findall(text):
            p = p.rstrip(".")
            if p == packet:
                cls = "packet"
            elif p == output or p.rstrip("/") == out_dir or out_dir.startswith(p.rstrip("/") + "/") and p.endswith(("chain_eval", "chain_eval/")):
                cls = "output"
            elif p.rstrip("/") == os.path.dirname(packet):
                cls = "packet"
            elif own_repair.search(p):
                cls = "repair"
            elif p.startswith(SYSTEM):
                cls = "system"
            elif SCRATCH_RE.match(p) or re.fullmatch(r"/tmp(/claude-1000(/[^/]+)?)?/?", p):
                cls = "scratch"
            else:
                cls = "outside"
                outside.append({"tool": name, "path": p, "context": text[:300]})
            classes[cls] += 1
        for rel in REL_OPEN_RE.findall(text):
            base = os.path.basename(rel)
            if base == os.path.basename(packet) or base == os.path.basename(output):
                classes["packet" if base == os.path.basename(packet) else "output"] += 1
            elif "/" not in rel and not re.search(r"RAN\d_(schema|text2)", rel):
                classes["scratch"] += 1
            else:
                classes["outside"] += 1
                outside.append({"tool": name, "path": rel, "context": text[:300]})
        for verb, arg in LIST_RE.findall(text):
            if verb == "find" and arg.startswith("("):
                continue
            listings.append({"command": f"{verb} {arg.strip()}"[:200]})
        for m in re.finditer(r"(RAN\d)_schema", text):
            if m.group(1) != wg:
                cross.append({"kind": "other packet", "context": text[max(0, m.start() - 80):m.end() + 20]})
        for m in re.finditer(r"(RAN\d)_(?:text2(?:sql|cypher)_)?run([A-J])", text):
            if (m.group(1), m.group(2)) != (wg, run):
                cross.append({"kind": "other run", "context": text[max(0, m.start() - 80):m.end() + 20]})
    sessions.append({
        "transcript": os.path.relpath(tp, root),
        "workingGroup": wg, "language": lang, "run": run,
        "packetWorkingGroup": pkt_wg,
        "nToolCalls": n_calls,
        "tools": dict(tools),
        "pathClasses": dict(classes),
        "outside": outside,
        "listings": listings,
        "crossReferences": cross,
    })

runs = collections.defaultdict(int)
for s in sessions:
    runs[(s["workingGroup"], s["language"], s["run"])] += 1
expected = [(w, l, r) for w in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5") for l in ("sql", "cypher") for r in "ABCDEFGHIJ"]
summary = {
    "nSessions": len(sessions),
    "nRunsCovered": sum(1 for k in expected if runs.get(k)),
    "runsWithoutTranscript": [list(k) for k in expected if not runs.get(k)],
    "nToolCalls": sum(s["nToolCalls"] for s in sessions),
    "pathClasses": dict(sum((collections.Counter(s["pathClasses"]) for s in sessions), collections.Counter())),
    "nOutside": sum(len(s["outside"]) for s in sessions),
    "nListings": sum(len(s["listings"]) for s in sessions),
    "nCrossReferences": sum(len(s["crossReferences"]) for s in sessions),
    "packetMatchesWorkingGroup": all(s["packetWorkingGroup"] == s["workingGroup"] for s in sessions),
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "sessions": sessions}, f, ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))

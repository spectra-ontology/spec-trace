"""Audit the final solver/query-writer subagent transcripts for data access outside the packet and the allowed tool.

usage: python3 audit_final_agents.py --scratchpad <dir> --subagents <dir> <final_agent_ids.tsv> [kind ...]
--scratchpad is the session scratchpad that held the prompts and the solvers' work directories;
--subagents is the directory with that session's agent-<id>.jsonl transcripts.
The allowed set is the paths named in the prompt and in every later coordinator message of the transcript.
Prints per agent: tool-use counts and every flagged access (path outside the allowed set, foreign --wg,
missing --text-only, network/db tokens, gold/item/sample tokens, Grep/Glob/Web tools).
"""
import argparse, collections, json, os, re
from pathlib import Path

ROOT = str(next(p for p in Path(__file__).resolve().parents if (p / ".git").exists()))
SP = ""
SUB = Path()
TOOL = "scripts/publication/paper/ongoing/sigir-2027-research/search_records_text.py"
PATH = re.compile(r"(?:/[\w.\-]+){2,}|(?:logs|ontology|scripts|docs|data)/[\w./\-]+")
RISK = re.compile(r"sample\.json|items_final|chain_items|admitted|gold|\.sqlite|sqlite3|neo4j|bolt:|:768\d|:769\d|qdrant|:6333|"
                  r"curl|wget|https?://|before_neutral|chain_eval/RAN\d_|_answers\.jsonl|responses/", re.I)


def expand(command):
    """Replace each $VAR by the latest shell VAR=/abs/path assignment made before it in the same command, then
    normalise `..` in the absolute paths this produces. Heredoc bodies are script text, not shell assignments,
    so they are blanked (same length) before assignments are collected."""
    shell = re.sub(r"(<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n)(.*?)(\n\2\b)",
                   lambda m: m.group(1) + " " * len(m.group(3)) + m.group(4), command, flags=re.S)
    assignments = [(m.end(), m.group(1), m.group(2))
                   for m in re.finditer(r"\b([A-Za-z_]\w*)=['\"]?(/[\w./\-]+)", shell)]

    def value(m):
        earlier = [v for end, name, v in assignments if name == m.group(1) and end <= m.start()]
        return earlier[-1] if earlier else m.group(0)

    expanded = re.sub(r"\$\{?([A-Za-z_]\w*)\}?", value, command)
    return re.sub(r"/(?:[\w.\-]+/)*\.\.(?:/[\w.\-]+)*",
                  lambda m: os.path.normpath(m.group(0)) if m.group(0).startswith(("/tmp/", ROOT)) else m.group(0),
                  expanded)


def own_paths(kind, wg, prompt_text):
    named = set(re.findall(r"(?:/tmp/claude-1000[\w./\-]+|logs/[\w./\-]+)", prompt_text))
    named = {p.rstrip(".") for p in named}
    allowed = set(named)
    if kind in ("text_search", "text_only", "abst_text_search", "abst_text_only"):
        cond = "text_only" if kind.endswith("text_only") else "text_search"
        base = "final_abst_text" if kind.startswith("abst_") else "final_text"
        allowed |= {f"{SP}/{base}/{cond}/work_{wg}", f"{SP}/{base}/{cond}/{wg}_answers.jsonl",
                    f"{SP}/{base}/{cond}/{wg}_trace.jsonl", TOOL, "scripts/common"}
    return allowed


def ok_path(p, allowed, kind, wg):
    if p.startswith(("/usr/", "/dev/", "/bin/", "/proc/self")) or p == ROOT:
        return True
    q = p[len(ROOT) + 1:] if p.startswith(ROOT + "/") else p
    if re.match(rf"/work_{wg}(/|$)", p) or re.fullmatch(rf"/{wg}_(answers|trace)\.jsonl", p):
        return True  # $S/work_<wg> style fragments of the agent's own work dir
    for a in allowed:
        a2 = a[len(ROOT) + 1:] if a.startswith(ROOT + "/") else a
        if q == a2 or q.startswith(a2.rstrip("/") + "/") or a2.startswith(q.rstrip("/") + "/"):
            return True
    # query writers may keep a small writer script directly in the scratchpad
    if kind in ("cypher", "sql", "abst_cypher") and re.fullmatch(re.escape(SP) + r"/[\w.\-]+\.py", p):
        return True
    return False


def main():
    global SP, SUB
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scratchpad", required=True)
    parser.add_argument("--subagents", type=Path, required=True)
    parser.add_argument("tsv", type=Path)
    parser.add_argument("kinds", nargs="*")
    args = parser.parse_args()
    SP, SUB = args.scratchpad.rstrip("/"), args.subagents
    rows = [l.split("\t") for l in args.tsv.read_text().splitlines() if l.strip()]
    kinds = set(args.kinds)
    for kind, wg, run, aid, _model, prompt in rows:
        if kinds and kind not in kinds:
            continue
        pp = Path(SP) / prompt.strip()
        pp = pp if pp.exists() else Path(SP) / "prompts_final" / pp.name
        # The prompt is also the transcript's first user message, which the loop below adds to `instructions`;
        # the file is only a second copy, so a scratchpad that has since been removed gives the same allowed set.
        prompt_text = pp.read_text() if pp.exists() else ""
        uses, instructions = [], [prompt_text]
        for line in (SUB / f"agent-{aid}.jsonl").open():
            try:
                r = json.loads(line)
            except Exception:
                continue
            content = (r.get("message") or {}).get("content")
            if r.get("type") == "assistant" and isinstance(content, list):
                uses += [(c["name"], c.get("input", {})) for c in content if c.get("type") == "tool_use"]
            # later coordinator messages (e.g. an execution-error repair round) may name further files to read or write
            if r.get("type") == "user":
                if isinstance(content, str):
                    instructions.append(content)
                elif isinstance(content, list):
                    instructions += [c["text"] for c in content if c.get("type") == "text"]
        allowed = own_paths(kind, wg, "\n".join(instructions))
        counts = collections.Counter(n for n, _ in uses)
        notes = collections.Counter()
        tool_runs = 0
        for n, inp in uses:
            if n in ("Grep", "Glob", "WebFetch", "WebSearch", "Agent"):
                notes[("tool", n + " " + json.dumps(inp)[:150])] += 1
            text = inp.get("command") or inp.get("file_path") or json.dumps(inp)
            if n in ("Read", "Write", "Edit") and not ok_path(inp.get("file_path", ""), allowed, kind, wg):
                notes[(n.lower(), inp.get("file_path", ""))] += 1
            if n == "Bash":
                for p in PATH.findall(expand(text)):
                    if not ok_path(p, allowed, kind, wg):
                        notes[("bash-path", p)] += 1
                for seg in re.split(r"[;&|\n]", text):
                    if "search_records_text.py" in seg and "--help" not in seg:
                        tool_runs += 1
                        w = {x.strip("'\"") for x in re.findall(r"--wg[ =](\S+)", seg)}
                        if w and w != {wg}:
                            notes[("foreign-wg", seg.strip()[:160])] += 1
                        if kind.endswith("text_only") and "--text-only" not in seg and "$" not in seg:
                            notes[("no-text-only", seg.strip()[:160])] += 1
            if n in ("Bash", "Read", "Write", "Edit"):
                body = text if n != "Write" else inp.get("file_path", "")
                for m in RISK.finditer(body):
                    ctx = body[max(0, m.start() - 50): m.end() + 50].replace("\n", " ")
                    notes[("risk-token", ctx)] += 1
        print(f"{kind}\t{wg}\t{run}\t{aid}\t{dict(counts)}\ttoolLines~{tool_runs}\tflags={sum(notes.values())}")
        for (k, v), c in sorted(notes.items()):
            print(f"    {c} {k} {v[:200]}")


if __name__ == "__main__":
    main()

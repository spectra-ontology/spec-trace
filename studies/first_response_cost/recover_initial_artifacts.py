#!/usr/bin/env python3
"""Recover four initial writer artifacts in a virtual filesystem from retained code.

Historical Python generators run with in-memory reads/writes, allowlisted imports
and a no-op os.makedirs. Shell commands, databases and APIs are never executed.
Only anonymous hashes and counts are written to the public receipt.
"""
import argparse
import ast
import builtins
import collections
import hashlib
import io
import json
import posixpath
from pathlib import Path
import re
import shlex
import types

RECIPES = {
    "1a210bfcef02bc6caf04e2c0d546e2e6c79b1c00cfa02e78643c26d3b847595b": {"generator_line": 32, "python_patch_line": 44},
    "8b35394b4466874ed018feb06935085a26cdbccc5d401150e4e2dff36e943a7b": {"generator_line": 40},
    "931c23aa8847a017579f62dacc12c3fc306c7aabea20aa56827678b3ff805974": {"generator_line": 40},
    "88f8cf863ceee3a35a5d7fbfe29ffd9d18bc7bf53e44f0070c27cac794792770": {"generator_line": 43, "sed_patch_line": 51},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(rows, line):
    tools = [v for v in rows[line - 1]["message"]["content"] if v.get("type") == "tool_use"]
    assert len(tools) == 1 and tools[0]["name"] == "Bash"
    return tools[0]["input"]["command"]


def python_block(text):
    match = re.search(r"<<'EOF'\n(.*?)\nEOF", text, re.S)
    assert match, "Historical heredoc missing"
    return match[1]


def virtual_run(code, packet_text, virtual, argv):
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Import):
            assert all(n.name in ("json", "re", "sys", "os") for n in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module == "collections" and all(n.name == "Counter" for n in node.names)
    modules = {"json": json, "re": re, "sys": types.SimpleNamespace(argv=argv),
        "os": types.SimpleNamespace(makedirs=lambda *a, **k: None, path=types.SimpleNamespace(dirname=posixpath.dirname)),
        "collections": types.SimpleNamespace(Counter=collections.Counter)}

    def safe_import(name, *args, **kwargs):
        assert name in modules, name
        return modules[name]

    class Output(io.StringIO):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def close(self):
            virtual[self.name] = self.getvalue()
            super().close()

    def safe_open(name, mode="r", *args, **kwargs):
        name = str(name)
        if mode == "w":
            assert name.endswith((".jsonl", ".py")), name
            return Output(name)
        assert mode == "r", mode
        if name.endswith("_schema.json"):
            return io.StringIO(packet_text)
        assert name in virtual, name
        return io.StringIO(virtual[name])

    safe_builtins = {k: v for k, v in vars(builtins).items() if k not in ("open", "exec", "eval", "compile", "input", "breakpoint", "__import__")}
    safe_builtins.update(open=safe_open, __import__=safe_import, print=lambda *a, **k: None)
    namespace = {"__builtins__": safe_builtins, "__name__": "__main__"}
    exec(compile(code, "<retained-generator>", "exec"), namespace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-base", type=Path, required=True)
    parser.add_argument("--transcript-root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    sessions = [json.loads(l) for l in (args.evidence / "sessions.jsonl").open()]
    by_agent = {r["provenance_agent_key"]: r for r in sessions}
    provenance = json.loads((args.source_base / "chain_eval/subagent_model_provenance.json").read_text())["conditions"]
    receipts = []
    for groups in provenance.values():
        for entries in groups.values():
            for entry in entries:
                agent = entry["agentId"]
                if sha(agent.encode()) not in RECIPES:
                    continue
                receipt = by_agent[sha(agent.encode())]
                path = args.transcript_root / entry["session"] / "subagents" / f"agent-{agent}.jsonl"
                raw = path.read_bytes()
                rows = [json.loads(l) for l in raw.splitlines()]
                recipe = RECIPES[sha(agent.encode())]
                text = command(rows, recipe["generator_line"])
                code = python_block(text)
                generator = re.search(r"cat > ([\w./-]+\.py)", text)[1]
                packet = args.source_base / receipt["binding"]["packet"]["path"].removeprefix("responses/")
                expected = args.source_base / receipt["binding"]["answers"]["path"].removeprefix("responses/")
                old_prefix = "/home/sihyeon/workspace/spectra/logs/publication/paper/ongoing/sigir-2027-research/"
                packet_arg = old_prefix + str(packet.relative_to(args.source_base))
                output_arg = old_prefix + str(expected.relative_to(args.source_base))
                virtual = {generator: code, "gen.py": code}
                if "python_patch_line" in recipe:
                    patch = python_block(command(rows, recipe["python_patch_line"]))
                    virtual_run(patch, packet.read_text(), virtual, ["patch.py"])
                    code = virtual["gen.py"]
                if "sed_patch_line" in recipe:
                    tokens = shlex.split(command(rows, recipe["sed_patch_line"]))
                    substitution = tokens[tokens.index("-i") + 1]
                    assert substitution.startswith("s/") and substitution.endswith("/")
                    before, after = substitution[2:-1].split("/")
                    before = re.sub(r"\\(.)", r"\1", before)
                    assert before in code
                    code = code.replace(before, after)
                virtual_run(code, packet.read_text(), virtual, [generator, packet_arg, output_arg])
                recovered = virtual[output_arg].encode()
                assert recovered == expected.read_bytes(), (receipt["route"], receipt["wg"], receipt["run"])
                receipts.append({"session_key": receipt["session_key"], "route": receipt["route"], "wg": receipt["wg"],
                    "run": receipt["run"], "transcript_sha256": sha(raw), "recipe": recipe,
                    "generator_as_executed_sha256": sha(code.encode()), "recovered_original_sha256": sha(recovered),
                    "recovered_bytes": len(recovered), "recovered_items": len(recovered.splitlines()),
                    "retained_original_bytes_equal": True, "original": receipt["binding"]["answers"],
                    "repair": receipt["binding"].get("separate_repair")})
    assert len(receipts) == 4
    (args.evidence / "initial_artifact_recovery.json").write_text(json.dumps({"scope": "all four writer sessions containing execution-feedback repair after first completion", "virtual_filesystem_only": True, "receipts": receipts}, indent=2) + "\n")
    manifest_path = args.evidence / "evidence_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    artifact = args.evidence / "initial_artifact_recovery.json"
    manifest[artifact.name] = {"sha256": sha(artifact.read_bytes()), "bytes": artifact.stat().st_size}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"recovered_artifacts": len(receipts), "all_byte_identical_to_retained_original": True}))


if __name__ == "__main__":
    main()

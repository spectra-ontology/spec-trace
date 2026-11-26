#!/usr/bin/env python3
"""Prepare answer-free packets and a prospective Codex factorial protocol.

This script performs no model generation, database execution, or scoring.
It reads the frozen writer packets, never the withheld gold answers.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").is_file())
BASE = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
STUDY = BASE / "release_preparation/vldb_release/studies/matched_domains"
MODELS = ("gpt-6.2-sol", "gpt-6.2-astra", "gpt-6.1-terra", "gpt-6-luna")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assert not (HERE / "protocol_lock.json").exists(), "Frozen protocol: create a new version instead."
    assert not (HERE / "submissions").exists(), "Generation already started."
    selection = json.loads((STUDY / "frozen/selection.json").read_text())
    original = {}
    for language in ("sql", "cypher"):
        original[language] = json.loads((STUDY / f"frozen/writer_{language}.txt").read_text().split("\n\n", 1)[1])
    assert [g["items"] for g in original["sql"]] == [g["items"] for g in original["cypher"]]
    assert collections.Counter(x["suite"] for x in selection) == {"main": 35, "extension": 15}
    order = [item["id"] for group in original["sql"] for item in group["items"]]
    assert len(set(order)) == len(order) == 50
    assert set(order) == {x["packetId"] for x in selection}
    packets = {}
    for language in ("sql", "cypher"):
        for condition in ("schema_only", "schema_domains"):
            groups = []
            for source in original[language]:
                group = {"wg": source["wg"], "schema": source["schema"],
                         "interface_mapping": source["categorical_domains"]["Encoding fact"],
                         "items": source["items"]}
                if condition == "schema_domains":
                    group["categorical_domains"] = {key: value for key, value in source["categorical_domains"].items()
                                                     if key != "Encoding fact"}
                groups.append(group)
            native = ("SQLite 3.37.2; SELECT statements only, WITH allowed; SELECT DISTINCT the requested fields in their given order."
                      if language == "sql" else
                      "Neo4j 5.26.0; read-only Cypher statements; RETURN DISTINCT the requested fields in their given order. No procedures or APOC.")
            instructions = (
                f"Write exactly one {language.upper() if language == 'sql' else 'Cypher'} query for each of the 50 items below. "
                "Each working group has its own database. Use only the supplied native schema, interface mapping, question, requested fields, "
                "and any supplied categorical domains. Record absence must be represented by an executable query returning no rows. "
                + native + "\n"
                'Return one JSON object {"queries":[{"id":"...","query":"..."}, ...]} in the supplied item order, with no prose or markdown. '
                "Use exact native stored values; source-verified dispositions, whole-document scopes, release editions, and chronological requests "
                "have the meanings specified by each question.\n"
                "This is a blind first submission. You may read only your exact assigned packet path and write only your exact assigned submission path "
                "specified in the assignment. Use file tools solely for those two actions; do not inspect other files, search the repository, use a network, "
                "a database, examples, other agents, prior queries, or execution feedback. Return your completed first submission directly or save it once "
                "to the assigned output path. Tools provide no query execution or answer feedback.\n\n"
            )
            name = language + "_" + condition
            write(HERE / f"packets/{name}.json", groups)
            (HERE / f"packets/{name}.txt").write_text(instructions + json.dumps(groups, ensure_ascii=False, separators=(",", ":")) + "\n")
            packets[name] = {"path": f"packets/{name}.txt", "sha256": sha(HERE / f"packets/{name}.txt"),
                             "jsonPath": f"packets/{name}.json", "jsonSha256": sha(HERE / f"packets/{name}.json")}
    # A balanced fixed assignment order; all A sessions precede all B sessions.
    # Distinct fresh sessions are used for every cell; assignments may overlap.
    cells = [("sql", "schema_only"), ("cypher", "schema_domains"),
             ("cypher", "schema_only"), ("sql", "schema_domains")]
    schedule = []
    for repetition in ("A", "B"):
        for step in range(4):
            for index, model in enumerate(MODELS):
                language, condition = cells[(step + index + (2 if repetition == "B" else 0)) % 4]
                schedule.append({"assignment": len(schedule) + 1, "group": "primary", "runId": f"{model}__{condition}__{language}_{repetition}",
                                 "requestedModel": model, "language": language, "condition": condition,
                                 "repetition": repetition, "packet": packets[language + "_" + condition]["path"]})
    write(HERE / "schedule.json", schedule)
    write(HERE / "cohort_manifest.json", {"packetOrder": order, "strata": selection})
    source_names = ["frozen/writer_sql.txt", "frozen/writer_cypher.txt", "frozen/selection.json",
                    "frozen/protocol.json", "frozen/categorical_domains.json", "rescore.py",
                    "evidence/meeting_identity_source.json"]
    sources = {str((STUDY / name).relative_to(ROOT)): sha(STUDY / name) for name in source_names}
    old_runner = HERE.parent.parent / "matched_interface/experiment.py"
    sources[str(old_runner.relative_to(ROOT))] = sha(old_runner)
    protocol = {
        "studyId": "codex-matched50-interfaces-domains-v1", "status": "prepared_pending_root_review",
        "preparedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "purpose": "Measure paired first-submission interface and categorical-documentation responses across four requested Codex model variants on the fixed matched cohort.",
        "requestedModels": list(MODELS), "reasoningEffort": "medium", "modelMetadataSource": "Available collaboration-tool model options in the current session, not a provider identity certificate.",
        "versionScope": "Exact selected versions available per requested family in this session. No6.1/6.2 Luna variant is offered here; gpt-6-luna is the requested Luna condition. This makes no claim about globally latest provider models. gpt-6.1-sol is excluded by user steering.",
        "additionalRequestedFamilies": {"families": ["Opus", "Fable", "Sonnet", "Haiku"],
                                        "status": "excluded_by_user_quota", "launchesPlanned": 0,
                                        "reason": "Latest user instruction excludes new Claude measurements because of subscription quota. Historical responses remain historical evidence only."},
        "identityPolicy": "Record requested model, session ID, returned execution metadata and any observed backend identity separately. Preserve unavailable actual identity as null; never infer it from generated self-identification. No fallback models.",
        "design": {"itemsPerRun": 50, "main": 35, "extension": 15, "languages": ["sql", "cypher"],
                   "conditions": ["schema_only", "schema_domains"], "repetitions": ["A", "B"],
                   "sessions": 32, "queries": 1600, "cohortSelection": "Unchanged historical fixed selector: minimum SHA256(anchor), then item ID, in each suite/WG/family cell of 667 main + 300 drawn extension candidates. All 15 selected extension items belong to admitted297.",
                   "samplingUnit": "Fixed family/WG representative; repeated sessions do not add new independent questions."},
        "generation": {"context": "Fresh context-isolated subject, fork_turns=none, no inherited discussion, gold, model responses or review material.",
                       "input": "One complete assigned packet, either inline or an exact assigned file path. Subject may read only that exact packet path and may write only its exact assigned output path once. No other filesystem access, repository search, delegation, skills, MCP, network, database access, query examples or feedback. Inspect observed tool traces against the two allowed paths; this is an audited instruction boundary, not a claimed operating-system isolation guarantee.",
                       "firstSubmission": "One final JSON object containing all50 queries. Preserve raw response and exact query text. No output-informed retries, repairs or rerolls. An invalid or incomplete first submission stays recorded and counts as unanswered for missing queries.",
                       "commonRequestedEffort": "medium", "fixedTaskBudget": "50 questions, one batch, one final submission, zero feedback. No numerical wall-clock or token cap is enforced by the subject tool; record actual elapsed time and returned usage when available.",
                       "tokenCap": None, "tokenCapReason": "The collaboration subject tool exposes requested reasoning effort but no enforceable token cap. Record returned usage when available.",
                       "parallelism": "Follow schedule assignment order; sessions may overlap within available slots. All16 Codex primaryA sessions commit or reach an administrative terminal state before primary scoring. B is prespecified for every cell and remains planned regardless of A outcomes. Until B completes, report replication pending. B subjects receive no A outcomes or revised prompts. Complete B independently of A scores when resources permit; record any administrative deferral explicitly.",
                       "unavailability": "Keep rejected/unavailable/timeout requests as separate administrative status. Do not substitute models or regenerate after a response. Transport failures before any response may be marked unavailable, not a model score."},
        "conditions": {"common": "Native frozen schemas, the same50 IDs/questions/fields/order, and the SQL scope to graph assessmentMethod JSON.scope interface mapping appear in both conditions.",
                       "difference": "schema_domains adds only the identical joint low-cardinality SQL/Cypher categorical-domain dictionaries. schema_only omits those dictionaries.",
                       "historicalComparison": "These newly controlled packets are a separate experiment. They are not identical to the historical667-item generation condition. Prior matched50 responses are historical context and never additional fresh replicates."},
        "execution": {"scorer": str(old_runner.relative_to(ROOT)), "scope": "Owner-only scoring after global commitment; original native queries executed once, no translated substitutes or repairs.",
                      "sql": "System python3 Python3.10.12 / SQLite3.37.2; hash-matched exports; mode=ro, PRAGMA query_only=ON.",
                      "cypher": "Neo4j5.26.0 existing read-only native services; verify server identity and categorical-domain agreement before scored execution.",
                      "caps": "60 seconds,2000 rows per query, requested field count.",
                      "services": "No service start, restart or configuration change by this harness. Owner coordinates any required service availability before execution. Preserve unavailable execution as blocked.",
                      "metrics": ["recorded exact unordered rowset", "recorded macro rowset F1", "meeting-identity exact/F1 using kept ran1#100-e", "strict raw rowset exact", "execution/completion status"],
                      "sourcePolicy": "Gold and meeting identity rules remain in the original owner-only scorer sources; subject packets contain neither."},
        "analysis": {"primary": "Within each requested model and language, per-item schema_domains minus schema_only identity exact and F1, separately for A/B and35main/15extension. Report paired discordant item counts.",
                     "secondary": "Within requested model/condition, paired Cypher-versus-SQL identity exact/F1; execution errors, missing first responses and family/WG cells.",
                     "uncertainty": "Descriptive fixed-cohort paired differences. Do not treat the50 strata as an IID sample or pool1600 query responses as independent. No claim of isolated provider/model architecture effect.",
                     "populationSeparation": "Report the50-item diagnostic in its own table/figure and caption. Do not append these results to the667-item Figure3 or claim a667/297 population estimate.",
                     "reporting": "Publish all prespecified available runs, raw first submissions, execution rows, provenance and paired outcomes, including null/negative results. Make interpretation after measurement."},
        "costPolicy": "Codex sessions only; no OpenRouter or paid per-call API experiments.",
        "sources": sources, "packets": packets, "scheduleSha256": sha(HERE / "schedule.json"),
        "cohortManifestSha256": sha(HERE / "cohort_manifest.json"), "queriesGeneratedBeforePreparation": 0
    }
    write(HERE / "protocol.json", protocol)
    print(json.dumps({"prepared": str(HERE), "sessions": len(schedule), "queries": len(schedule)*50,
                      "packetHashes": {k: v["sha256"] for k, v in packets.items()}}))


if __name__ == "__main__":
    main()

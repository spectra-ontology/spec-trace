# Replay the frozen source and score named records

All five deposited body TTLs have been restored into isolated Neo4j 5.26.0
instances. Actual measurements reproduce **966,859 nodes and 4,908,850
relationships**, including every label/type inventory count, with no detected
parser property conflict. Source sizes, MD5s and SHA256s match the archived
Zenodo 2.0.0 checksum record. See the
[restoration manifest](frozen_ttl_import_manifest_v1.json) and
[gold-free complete schema](source_schema_frozen_v1.json).

The [compiled tasks](prospective_task_definitions_v2.json) and
[typed frozen references](prospective_reference_gold_frozen_v2.json) contain
**36 eligible of 40 selected new task variants**. The other IDs remain recorded:
one unresolved definition and three complete outputs exceeding 2,000 rows.
Use [the audit guide](README_contract_audit.md) for original-question provenance,
47-versus-25 audit scope, and the unchanged 624-item release.

## Quickstart

Run from the repository root with Python 3.11, the Neo4j driver and `jsonschema`
available, Docker, and a local `neo4j:5.26.0` image. Obtain the five unchanged
`RAN*-body.ttl` files through the
[release artifact inventory](../../kg/per_wg/README.md) and place them in
`release_package/kg/per_wg/`. The wrapper never downloads an image or reads
operational database credentials. Use fresh output filenames for replay files.

1. Restore each WG into a fresh owned instance. This example loads RAN3; repeat
   with the corresponding WG/file/checksum from the table below.

```sh
python release_package/cqs/contract_repair_v1/load_frozen_ttl_neo4j.py \
  --wg RAN3 --ttl release_package/kg/per_wg/RAN3-body.ttl \
  --expected-md5 ad73158bf9d80b1e3b875edaa9ea7ded
```

| WG | Deposited MD5 |
|---|---|
| RAN1 | d0cd98857f936c6fbccaa190e1fc365c |
| RAN2 | ec7dfb70a0822e47e78765172117d87f |
| RAN3 | ad73158bf9d80b1e3b875edaa9ea7ded |
| RAN4 | 8c1b8f4b3d6b6368a491ba9dbc7a4399 |
| RAN5 | e60edcc16b3e96bbe0d70f54fb0adbc3 |

2. Once all five instances are ready, replay the pinned compiled definitions.
   The runner uses read-only transactions and retains every selected disposition.

```sh
python release_package/cqs/contract_repair_v1/execute_frozen_reference_gold.py \
  release_package/cqs/contract_repair_v1/prospective_task_definitions_v2.json \
  reference_replay_local.json
```

3. Put one variant's prediction in `prediction.json` as
   `{"records": [{"tdocNumber": "..."}]}`. The following standalone example
   compares an eligible task against its saved typed reference. It requires
   exact field names/types and the task's set/sequence semantics.

```python
import json, sys
from pathlib import Path

base = Path("release_package/cqs/contract_repair_v1")
sys.path.insert(0, str(base))
from score_contract import score_contract

item_id = "RAN1_P1_CQ1-1"
task = next(t for t in json.loads((base / "prospective_task_definitions_v2.json")
            .read_text())["items"] if t["id"] == item_id)
reference = next(g for g in json.loads((base / "prospective_reference_gold_frozen_v2.json")
                 .read_text())["items"] if g["id"] == item_id)
assert reference["eligible"], "Unresolved or capped references cannot be scored"
fields = [{**{k: f[k] for k in ("name", "type", "role", "nullable") if k in f},
           "source_anchor": task["task_question"]} for f in task["required_fields"]]
contract = {"version": 1, "item_id": task["variant_id"], "status": "ready",
            "required_fields": fields, "collection": {"kind": task["collection_kind"]},
            "constraints": [], "unresolved_reasons": []}
prediction = json.loads(Path("prediction.json").read_text())
result = score_contract(contract, reference["execution"]["rows"], prediction)
print(json.dumps({k: result[k] for k in
      ("output_exact", "partial_named_cells", "output_full_records")}, indent=2))
```

These are comparisons of supplied records for the explicit graph task. Nested
JSON fields also have `json_schema` in the compiled definitions; use
`typed_json.matches` to check their shape and retain their internal ordering.
For original-question checks, use each ledger item's `typed_contract`; do not
replace its unresolved scope with the example's new-task contract. To rerun the
initial25 schema/raw-saved-gold checks without altering the archived reports:

```sh
python release_package/cqs/contract_repair_v1/validate_ledger.py \
  --out ledger_validation_local.json
```

## Source and execution safeguards

The wrapper reuses the unchanged shipped
[restoration loader](../../pipeline/load_released_kg.py): one RDF subject per
node, all labels, typed literal properties and exact relationship-name inversion,
including escaped `definedInSection` and `disjointWith`. It creates only
`kdd-db-frozen-v1-ran1` through `ran5`, exposing Bolt on loopback ports 57687–57691
with authentication disabled only for these local instances. The reference
runner connects with `auth=None`; existing research database credentials are
irrelevant. Targets must be new, owned, empty and correctly bound before writes;
there is no DELETE/WIPE in the shipped loader. Per-container limits are one CPU,
2 GiB memory, 512 MiB heap and 256 MiB page cache. Imports are sequential and the
statement-stream parser's materialized dictionary/set is limited to 8 GiB address
space. Actual maximum wrapper RSS was 2,175,584 KiB. Local data and logs remain
under `_frozen_ttl_v1`, excluded from this checkout's Git index; exclude that
work directory in a new checkout before staging. The public manifest omits ownership UUIDs, private paths and server addresses.

The complete schema exports labels, all endpoint-label relationship triples and
property names/type sets without populations, sample values, gold or task
queries; auxiliary loader `iri` is omitted. Only this schema, a task question
and its output definition may enter a structured reader. Gold, QA files,
reference queries, source counts and restoration inventory are evaluation-only.
The frozen task/reference/source/schema hashes must be pinned before generation.

Restoration fidelity and 36/40 typed-reference eligibility do not certify
external semantics, causal claims, original-question validity or performance
across Core560. The remaining four IDs are not replaced or silently truncated.
Human and independent domain-expert validation remain zero. Current operational
Neo4j pilot data differ from the deposited snapshot and are not primary gold;
new model predictions must target the separately defined variants. This package
does not certify snapshot/cutoff alignment of a separate retrieval corpus.
Reader/model execution and measured performance are separate artifacts.

# SPECTRA artifact walkthrough

This guide connects the process dataset, current question contracts and measured
model outputs to their reproducible checks. Run commands from the **repository
root**. The [current Core index](cqs/current_core/README.md) selects **522 verified
contracts**; the [complete register](cqs/core_disposition_audit/README.md) accounts
for all 560 Core IDs as **522 verified, 21 clarification diagnostics, 17
frozen-input-dependent diagnostics and 0 pending**.

## Choose a replay level

| Goal | Released inputs | Entry point |
| --- | --- | --- |
| Check files, ontology and examples | Git checkout; `rdflib` and `pyshacl` | Quick release gate below |
| Verify current contracts and saved scores | Git checkout; Python 3.10 or later | Current launcher and individual cohort replays |
| Rebuild graph data and execute references | Archived body graphs and a scratch database | [Full reconstruction guide](tests/README.md) |

## Current benchmark and measured examples

The current contracts cover record/decision retrieval, process aggregation and
decision/study-to-standard tracing. Each active definition pins the original
question, typed answer shape, source witnesses, reference outputs, semantic
reviews and scorer controls.

```bash
python3 -B -I release_package/cqs/verify_current_release.py
```

This launcher checks the current index, complete disposition register and saved
evaluations 23–51. It uses released evidence without model, network or database
execution. The [N=12 process-question cohort](cqs/original_core_overnight_evaluation15/README.md)
and [N=3 named-record cohort](cqs/original_core_overnight_evaluation24/README.md)
provide their exact standalone saved-score commands. Each evaluation preserves
its own inputs, model protocol, first responses and denominator, including
errors and abstentions. The [cohort catalogue](cqs/current_core/README.md#evidence-catalogue)
links the complete measurement history.

## File and schema fast path

```bash
pip install rdflib pyshacl
python3 -B release_package/tests/verify_benchmark.py --quick --out /tmp/spectra-quick-check
```

The quick gate contains 52 checks: 48 file-level checks plus four benchmark
checks. A Git-only checkout executes 47; the five per-WG body-text checks run
when deposited graphs are placed in `release_package/kg/per_wg/`. Successful
Git-only output ends with `=== QUICK: 47/47 checks passed ===`.

The underlying file-only command is:

```bash
python3 -B release_package/tests/verify_release.py
```

It writes no report and returns exit 0 when every executed check passes. Its
eleven labelled sections (1, 1b, 2, 2b, 3, 4, 5, 6, 7, 8, 8b) cover ontology
parsing, documentation byte identity, SHACL on synthetic and process examples,
end-to-end SPARQL, original benchmark inventory/gold, structural metrics,
validation references, synthetic-instance checks, release inventory and body/schema
graphs. Body checks print `[SKIP]` in a Git-only checkout and leave the total.

## Inspect individual dataset checks

### Ontology and structural metrics

```bash
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('release_package/ontology/spectra.ttl', format='turtle'); print(f'Triples: {len(g)}')"
python3 -B release_package/tests/reproduce_structural_metrics.py
```

Expected ontology totals: 914 triples; 32 classes; 53 object properties;
81 data properties; 20 functional and 2 inverse-functional properties;
15 inverse pairs; 6 irreflexive and 2 asymmetric properties; 15 subclass axioms.
The structural-metric script checks the released JSON and exits 0 on agreement.
Protégé can open `release_package/ontology/spectra.ttl` for visual inspection.

### SHACL and the synthetic traceability example

```bash
pyshacl -s release_package/shapes/spectra-core.shacl.ttl release_package/examples/instantiation_snippet.ttl
python3 -B release_package/tests/test_e2e_sparql.py
```

Expected: SHACL `Conforms: True`; the SPARQL example reports 933 triples,
returns the expected R1-2599998 / RAN1#121 record and prints `PASS`.
The [example directory](examples/end_to_end/README.md) contains data, queries
and expected output. The [tutorial](TUTORIAL.md) shows how to reuse the schema.

### Original question collection and stored gold

The original `cqs/spectra_cq_v2.0/questions.json` preserves 624 released questions
from 654 authored questions, with 30 held out and 624 stored gold statuses PASS.
Released counts are RAN1 142, RAN2 128, RAN3 123, RAN4 117 and RAN5 114.
The example query directories contain 15 Cypher and 6 SPARQL queries;
MULTI_HOP_traceability is available in both.

These original query-derived answer sets have their own snapshot. The current
522 contracts and typed scorers are selected separately through the current index.
[validation/cq_replay/](validation/cq_replay/) records scratch-load graph counts,
per-WG reports, 624/624 original gold matches and 142/142 RAN1 SPARQL row-count
parity. Full original-reference execution uses the deposited per-WG graphs and
the [scratch-store procedure](tests/README.md). Its `--full` command wipes the
target database, so supply a dedicated scratch instance.

## Follow quantitative evidence to its source

[validation/validation_manifest.md](validation/validation_manifest.md) maps
quantitative dataset claims to the released JSON fields. The validation directory
contains 15 JSON evidence files, replay records, chart/source-fidelity notes and
the manifest. RAN1 instance counts, cross-WG schema differences and OOPS output
are retained build snapshots; the ontology, SHACL and synthetic SPARQL checks
above recompute their specific released-artifact properties.

[reproduce_scenario_counts.py](tests/reproduce_scenario_counts.py) additionally
recounts all 18 cross-WG scenarios on the archived body graphs. Seventeen agree
with the earlier deployed snapshot. RAN3 TS38.300 CRs are 1,249 on the released
graph versus 270 on the deployed snapshot; both populations and the difference
are recorded in the manifest. See [tests/README.md](tests/README.md) for graph
placement and the `--ttl-dir` option.

Current contracts link their complete native records, independent SQL results,
source evidence and scorer controls. Review provenance records two separate
nonblind AI semantic reviews and human/expert n=0. The [complete disposition
register](cqs/core_disposition_audit/README.md) reproduces source-linked
specification diagnostics alongside executable answers.

## Data placement and historical measurements

The [body-graph inventory](kg/per_wg/README.md) links the version 2.0.0 deposit.
Git supplies the ontology, process metadata, contracts and retained evaluation
artifacts; archived body graphs support full dataset reconstruction. Saved-score
replay uses saved outputs and contexts. Fresh retrieval ranking additionally
uses the original full-text corpus outside the deposit.

The [evaluation scope guide](cqs/contract_repair_v1/README_evaluation_scopes.md),
[historical baseline documentation](../paper/baseline/README.md) and [source
supplement guide](cqs/source_supplements_README.md) preserve earlier scorer
families and separately declared input snapshots. Cite the actual Git commit
and linked immutable cohort for a current contract or measured result.

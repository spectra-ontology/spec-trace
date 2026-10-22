# SPECTRA: tracing the 3GPP standardization process

SPECTRA connects technical contributions, recorded meeting decisions, change
requests and specification structure across all five 3GPP RAN working groups.
Its shared process model turns document registers, meeting reports and
specification metadata into executable process queries with inspectable sources.

The release contains **966,859 nodes, 4,908,850 relationships and 12,931,842
RDF triples**. SpectraCQ preserves **624 original questions**. Its complete
560-question Core register provides **522 verified contracts**, **21
clarification diagnostics** and **17 frozen-input-dependent source-role
diagnostics**. Every original Core ID has a completed disposition. The
[counts manifest](release_package/MANIFEST.md) links dataset totals to their artifacts.

Start with the [current Core index](release_package/cqs/current_core/README.md)
for executable tasks, or the [release package](release_package/README.md) for
the ontology, graph data and construction pipeline.

## Three process-analysis task families

The [32-class ontology](release_package/ontology/spectra.ttl) represents submissions,
resolutions, liaison routing, CR metadata and specification targets. Explicit
references, shared-meeting context and declared clause targets retain distinct
roles. Each verified contract fixes requested fields and types, collection and
ranking rules, reference records and source-linked checks.

| Research task | Worked examples |
| --- | --- |
| **Recover records and recorded technical decisions** | [Named TDoc/CR metadata](release_package/cqs/original_core_overnight_repairs24/README.md), [PDCCH decision content](release_package/cqs/original_core_overnight_repairs32/README.md) and [complete approved-change reasons/summaries](release_package/cqs/original_core_overnight_repairs41/README.md) |
| **Aggregate activity and compare contribution patterns** | [Exact Agreement activity count](release_package/cqs/original_core_overnight_repairs50/README.md), [Work Item company rankings with boundary ties](release_package/cqs/original_core_overnight_repairs_auth37/README.md) and [meeting-level documentary trends](release_package/cqs/original_core_overnight_repairs38/README.md) |
| **Trace decisions and studies to standards** | [Decision-to-Spec selection](release_package/cqs/original_core_overnight_repairs39/README.md), [CR affected-clause records](release_package/cqs/original_core_overnight_repairs36/README.md), [cross-spec count/sample answers](release_package/cqs/original_core_overnight_repairs48/README.md) and [URLLC implementation details](release_package/cqs/original_core_overnight_repairs51/README.md) |

These examples expose complete answer shapes, selection boundaries and source
roles. The URLLC case reconstructs two detailed specification records through the
joint TR38.824/TR38.825 implementation program. Its complete 72-CR retained
candidate census is checked alongside 41 original documents; 35 CRs supply 74
source text components across 70 CR–field records. Independent SQL, graph
interpretation and native execution agree on both records and every component.
The [current index](release_package/cqs/current_core/README.md) connects all
522 active contracts to their pinned evidence and available saved evaluations.

## Measured evaluation examples

The four-method protocol compares generated Cypher and SQL over structured
records with single and two-round retrieval over bounded text contexts. These
two separately registered cohorts preserve their own questions, inputs, first
responses and denominators.

| Method | Complete-record macro F1, N=12 | Complete-record macro F1, N=3 |
| --- | ---: | ---: |
| Text2Cypher | 0.5833 | 1.0000 |
| Text2SQL | 0.4333 | 1.0000 |
| Single retrieval | 0.0000 | 0.0000 |
| Two-round retrieval | 0.0833 | 0.3333 |

In the [twelve-question cohort](release_package/cqs/original_core_overnight_evaluation15/README.md),
Cypher has five exact outputs and SQL four. In the [named-record cohort](release_package/cqs/original_core_overnight_evaluation24/README.md),
both structured methods return all complete requested records. Every method
retains all cohort items in its denominator, including errors and abstentions.
The packages retain actual information access, prompts, first responses,
execution results and complete-record score replays. These measured results
describe their stated cohorts; the 522-contract index describes benchmark
definitions and their evidence.

## Reproduce from a Git checkout

Run from the repository root. The file/schema checks need `rdflib` and
`pyshacl`; current saved-evidence replay uses Python 3.10 or later.

```bash
pip install rdflib pyshacl
python3 -B release_package/tests/verify_benchmark.py --quick --out /tmp/spectra-quick-check
python3 -B -I release_package/cqs/verify_current_release.py
```

| Replay level | Entry point and inputs |
| --- | --- |
| File and schema checks | The quick gate checks Git-distributed files; five additional checks use the body-graph deposit. |
| Current contracts and saved scores | The current launcher checks the index, complete disposition register and saved evaluations 23–51 without model or database calls. Individual cohort READMEs supply exact standalone replay commands, including N=12 and N=3. |
| Rebuild graphs and execute references | The [test guide](release_package/tests/README.md) describes body-graph placement and full reference execution in a scratch database; the [pipeline](release_package/pipeline/README.md) documents construction. |

The [artifact walkthrough](release_package/ARTIFACT.md) connects these layers to
the released checks. Saved-score replay uses retained responses and contexts.
Fresh passage ranking uses the original full-text corpus, which is outside the
deposited artifacts. Use a new output filename for score replays that refuse to
overwrite reports.

## Get the data

Git includes the ontology, metadata-only process graphs, construction code,
benchmark contracts and retained evaluation evidence. The five larger
`RAN{1..5}-body.ttl` graphs are available in the [version 2.0.0 deposit](https://doi.org/10.5281/zenodo.21504833).
The [body-graph inventory](release_package/kg/per_wg/README.md) gives placement,
counts and source-quality annotations.

The [concept DOI](https://doi.org/10.5281/zenodo.20034871) locates archived versions.
Later Git additions have their own commit references. The ontology is version
1.1.1, with persistent identifier [w3id.org/spectra](https://w3id.org/spectra).

## Evidence catalogue and earlier experiments

The [current Core catalogue](release_package/cqs/current_core/README.md#evidence-catalogue)
retains every linked contract/evaluation cohort and detailed source populations.
The [all-560 register](release_package/cqs/core_disposition_audit/README.md)
connects the 522 executable contracts and 38 completed diagnostics to their
original question identities.

[Historical analyses](paper/baseline/README.md) and the [evaluation scope guide](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md)
preserve original and revised scoring definitions. The [source supplement guide](release_package/cqs/source_supplements_README.md)
indexes changed-input experiments, including [RAN2 summaries](release_package/cqs/original_core_source_RAN2_CR_summary240_evaluation/README.md)
and [RAN3 summaries](release_package/cqs/original_core_source_RAN3_CR_summary202_evaluation/README.md).
Earlier retained diagnostics remain directly replayable: [31-item source-aligned outputs](release_package/cqs/contract_repair_v1/original_source_aligned/README.md)
and [strict named-record task variants](release_package/cqs/contract_repair_v1/README.md).
Each linked experiment retains its original snapshot, task definition and denominator.

## Citation and license

Use [CITATION.cff](release_package/CITATION.cff), [CodeMeta](release_package/codemeta.json)
or the [SpectraCQ citation](release_package/cqs/spectra_cq_v2.0/citation.bib).
SPECTRA-authored components use CC BY 4.0; derived 3GPP text retains separate
source attribution under the [package license](release_package/LICENSE).

Maintainer: Sihyeon Choi, Samsung Electronics. Questions and corrections:
[repository issues](https://github.com/spectra-ontology/spec-trace/issues).

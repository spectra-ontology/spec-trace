# Disposition scope across the ontology, graph and SQLite

SPECTRA records the reach of a decision on the assertion linking a meeting decision to a particular target document. The same disposition scope is available in the released JSON-LD, on the graph node and in SQLite. A resolution's event marker identifies the kind of source entry that supplied the meeting decision. [OWL model](../docs/spectra.ttl) · [SHACL shapes](../docs/spectra-shapes.ttl) · [Reading codebook](../studies/disposition_reading/codebook.md#scope)

| Meaning | OWL and JSON-LD | Native graph | SQLite | Check |
|---|---|---|---|---|
| **Reach of a decision on the named target** | `DecisionDisposition` specializes `EvidenceAssertion`. The `assessmentMethod` string contains a JSON `scope` key with `whole_target` (entire document), `subdocument` (part or adoption into another document), or `undetermined` (source passage gives insufficient scope evidence). | `DecisionDisposition.assessmentMethod` preserves that string. `DISPOSITION_OF` links the assertion to the resolution and `DISPOSITION_TARGET` links it to the document. | `disposition.scope` is the parsed JSON key. `disposition.resolution_id` identifies the resolution. | `EvidenceAssertionShape` checks one nonempty `xsd:string`; the builder assigns the JSON key and the SQLite exporter parses it. The check below validates the nested value and its projection for every released record. |
| **Source meeting decision from a document entry** | `Resolution.resolutionScope` holds `document_disposition` for a decision recorded in a source report's document entry. | `Resolution.resolutionScope` preserves the event marker. | The `resolution` table projects the resolution ID and meeting ID. | `ResolutionScopeShape` targets records carrying the property and checks one permitted `xsd:string` value, `document_disposition`. |
| **Research scope stated in a technical report** | `spectra:scope` is text on `TechnicalReport`. | Technical-report text. | Outside the chain-query projection. | The OWL property defines its `TechnicalReport` domain and string range. |

The [disposition builder](../code/scripts/tsg/RAN/formal/common/decision_disposition.py) sets `undetermined` for ambiguous outcomes and `subdocument` for partial agreement or a predicate about specific content. The [document-event builder](../code/scripts/tsg/RAN/formal/common/document_decision_storage.py) assigns the resolution marker. The [SQLite exporter](../code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/export_chain_records_sqlite.py) writes the extracted key to its own column. Disposition-based benchmark rows use `d.evidence_status = 'source_verified' AND d.scope = 'whole_target'` under the conditions listed for each family. [Answer contract](../benchmark/ANSWER_CONTRACT.md)

## Worked record

The U003 example links disposition `RAN5:DOC-107-R5-253194-b8632:R5-253194` to the source entry for CR 5008. The disposition's `assessmentMethod` contains `"scope": "whole_target"`. Its `dispositionOf` points to `tdoc:resolution/DOC-107-R5-253194-b8632`, whose event marker is `document_disposition` and whose meeting is RAN5 #107. The SQLite row stores the parsed scope and the same resolution ID. [Disposition record and source location](../studies/practitioner_questions/decomposition/source_record.json) · [RAN5 document-entry resolutions](../records/phase-2/RAN5/resolutions_document_dispositions.jsonld)

Across the released graph records, dispositions linked to marked resolutions span all three target scopes. They include 330,405 `whole_target`, 130 `subdocument` and 21,540 `undetermined` records.

## Verification evidence

| Procedure | Coverage and what it checks |
|---|---|
| Source binding and location | A fixed-seed audit matches 2,500 file hashes and locates all sampled quote fragments with symbol-aware matching. The rich-text check locates 333,171 of 333,539 source-verified quotes, and the accepted-prose projection resolves the other 368 at their stored spans. These checks bind records to passages. [Sample audit](../responses/final/decision_disposition_audit.json) · [Locator replay and follow-up](../diagnosis/source_locator/README.md) |
| Deterministic checks | The disposition audits compare recorded codes with rules for source decision fields and list-line outcome patterns. The coverage and disagreements are reported by working group. [Decision field audit](../responses/final/decision_disposition_audit.json) · [List-line audit](../responses/list_line_disposition_audit.json) |
| Recorded readings with labels withheld | Claude Code subagent and Codex CLI (`gpt-6.1-sol`) sessions, one per part for each reader, read 1,000 sampled source-verified records. The two sets of labels agree on 985 codes (κ = 0.980528), support 997 and jointly contradict 3. At least one reader gives the stored scope for 994 of the 997 code-supported records. The intervals in the study quantify joint-reader contradictions under this protocol. [Study, packets and replay](../studies/disposition_reading/README.md) |
| Finite source-only identity inspection | Codex inspected all 233 dispositions (242 evidence uses in 99 main items) whose evidence depends on stored report-entry identity comparisons. It reads the governing report text, target row and CR cover fields, and matches all 233 stored target attributions, codes and scopes. The original build separately records 3,684 identity comparisons from a deterministic script and 9,884 with performer identities unrecorded. [Inspection, packets and replay](../studies/disposition_reading/finite_identity/README.md) |
| Representation and evidence-use replay | The script below compares the JSON-LD and SQLite by disposition ID, tallies dispositions linked to a marked graph resolution, and checks whether the three jointly contradicted disposition IDs contribute to main-item gold evidence. [Machine-readable result](scope_mapping_checks.json) |

The 1,000 source-verified records include 979 `whole_target` and 21 `subdocument` scopes. Among code-supported records, at least one reader gives the stored scope for 975 of 977 `whole_target` and 19 of 20 `subdocument` records. Stored codes in this sample span 13 of the 16 formal codes. The least frequent observed codes are `not_concluded` (1), `not_agreed` (2), `conditionally_agreed` (3), `merged` (4) and `partially_agreed` (6). The sample contains zero `rejected`, `replied_to` and `ambiguous` records. [Sample keys](../studies/disposition_reading/keys.json) · [Reader A](../studies/disposition_reading/readings/A.jsonl) · [Reader B](../studies/disposition_reading/readings/B.jsonl) · [Complete population by code](decision_codes.md)

### The three jointly contradicted cases

| Packet and target | Stored code and scope | Both readers | Archived follow-up interpretation | Main gold uses of the disposition ID |
|---|---|---|---|---:|
| `c87d64678426`, `R1-161376` | `agreed`, `whole_target` | `noted` | Rel-12 CR0583 is the target of agreement. The passage also records a different document as noted. | 0 |
| `acecb67d626d`, `R2-2501405` | `agreed`, `whole_target` | `revised` | The meeting agreement precedes a coversheet revision into `R2-2501599`. | 0 |
| `f18b2657d0d3`, `R1-2409575` | `partially_agreed`, `subdocument` | `agreed` | Content was adopted into an alignment CR. The archived follow-up identifies this as a partial-agreement codebook boundary. | 0 |

The follow-up performer was unrecorded. The archive preserves the original blind labels and comparisons separately from this reading of the cases. The evidence-use replay checks 1,640 disposition references across the 667 main items. [Exact disposition IDs and archived follow-ups](../studies/disposition_reading/followups.json) · [Core gold](../benchmark/items_final/gate/core/chain_items_admitted.jsonl) · [RAN5 gold](../benchmark/items_final/gate/ran5/chain_items_admitted.jsonl)

## Run the representation check

All 358,062 released JSON-LD dispositions match the SQLite projection on ID, resolution ID, decision scope and evidence status. The comparison covers 331,932 `whole_target`, 1,607 `subdocument` and 24,523 `undetermined` records. The checker uses the Python standard library and reads one working-group database at a time in read-only mode. [Checker](check_scope_mapping.py) · [Replayed counts](scope_mapping_checks.json)

Run from the release root to compare the regenerated output with the packaged result.

```sh
mkdir -p work
python3 -B ontology/check_scope_mapping.py --release . > work/scope_mapping_checks.json
diff -u ontology/scope_mapping_checks.json work/scope_mapping_checks.json
```

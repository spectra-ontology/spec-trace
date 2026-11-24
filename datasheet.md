# Datasheet: traceability records and the TraceChain benchmark

This datasheet follows the questions of Gebru et al., "Datasheets for Datasets", *Communications of the ACM* 64(12):86–92, doi:10.1145/3458723. Every count below was measured on the files of this package.

| Path | Content |
|---|---|
| `records/` | JSON-LD record files of RAN1 to RAN5 |
| `sqlite/` | one SQLite database per working group, with `SHA256SUMS.txt` |
| `receipts/` | identity-review receipts |
| `ontology/` | the OWL ontology and its SHACL shapes |
| `benchmark/` | drawn and admitted benchmark items, gate reports, anchor lists, five-hop sets |
| `abstention/` | abstention items, their checks, stored responses and scores |
| `responses/` | stored responses, queries, scores and the result files of the audits and analyses |
| `diagnosis/` | per-item diagnosis of agent misses |
| `code/` | build, benchmark, gate, scoring, audit and analysis scripts |
| `sources/manifest.jsonl` | archive URL and hashes of each cited meeting report |
| `restore/restore_sources.py` | restores the cited meeting reports from the public 3GPP archive |
| the root-level redaction lists | one row per released file that differs from its original, with the SHA-256 of both |

## 1. Motivation

**Purpose.** The package supports the evaluation of retrieval and query systems on *chain questions* over the standardization records of the five 3GPP Radio Access Network working groups, RAN1 to RAN5. A chain question asks for the documentary path from a contribution (a TDoc or a change request) to a working-group decision, a plenary CR pack, a plenary meeting and a specification clause. Its answer is a set of rows of identifiers and codes.

The records also support research on building source-bound records from meeting reports. Each source-verified disposition carries the file hash, the locator and the sentence rule that assign its code.

**Creators.** Sihyeon Choi, Junho Lee and Jungmin Park, Samsung Electronics.

## 2. Composition

**Instances.**

1. *Records* of documents, meetings, resolutions, dispositions, CR packs, clauses and the links between them, one partition per working group, in JSON-LD (`records/`) and SQLite (`sqlite/`).
2. *Identity-review receipts* (`receipts/`), cited by the disposition records where a report entry and the document list describe the same document differently.
3. *Benchmark items* (`benchmark/`), each with a question, the requested fields, gold rows and evidence.
4. *Abstention items* (`abstention/`), each with the gold class `answer`, `none` (empty answer) or `insufficient` (the records lack the needed fact).
5. *Stored responses, scores and analysis results* (`responses/`, `diagnosis/`) of every evaluated condition.

**Record counts.** SQLite row counts, equal to the JSON-LD node counts:

| WG | Documents | Dispositions (source-verified) | Resolutions | Revision links | Meetings | CR packs | CR-in-pack links | Clauses | CR-to-clause links |
|---|---|---|---|---|---|---|---|---|---|
| RAN1 | 127,149 | 22,649 (13,437) | 42,767 | 12,000 | 62 | 522 | 2,120 | 1,621 | 6,141 |
| RAN2 | 124,271 | 47,236 (35,715) | 49,797 | 22,370 | 61 | 602 | 5,939 | 3,798 | 12,732 |
| RAN3 | 60,566 | 58,512 (58,161) | 61,105 | 15,690 | 60 | 463 | 3,038 | 3,972 | 10,064 |
| RAN4 | 174,739 | 164,176 (160,824) | 168,499 | 23,393 | 61 | 1,328 | 13,952 | 18,334 | 38,102 |
| RAN5 | 65,413 | 65,489 (65,402) | 65,483 | 18,367 | 37 | 1,430 | 29,438 | 13,612 | 38,324 |
| Total | 552,138 | 358,062 (333,539) | 387,651 | 91,820 | 281 | 4,345 | 54,487 | 41,337 | 105,363 |

1. *Resolutions:* 348,952 document dispositions, 33,509 agreements, 3,569 conclusions and 1,621 working assumptions.
2. *Disposition codes:* 16 distinct codes, from `agreed` to `withdrawn`.
3. *Disposition scope:* 331,932 dispositions apply to the whole target and 1,607 to part of a document. The other 24,523 have the status `pending` and the scope `undetermined`, which marks the dispositions to which the source-verification rule assigned no code.

**Coverage.** The records cover 281 working-group meetings:

| WG | Meetings | Records |
|---|---|---|
| RAN1 | #84 to #124b | 62 |
| RAN2 | #93 to #134 | 61 |
| RAN3 | #91 to #132 | 60 |
| RAN4 | #78 to #119 | 61 |
| RAN5 | #76 to #112 | 37 |

Clause records span Release 15 to Release 19:

| Release | Clause records |
|---|---|
| Rel-15 | 4,402 |
| Rel-16 | 6,180 |
| Rel-17 | 8,213 |
| Rel-18 | 11,621 |
| Rel-19 | 10,921 |

Source-verified dispositions cite 276 meeting reports: 61 in RAN1, 61 in RAN2, 56 in RAN3, 61 in RAN4 and 37 in RAN5.

**Benchmark items.** Items were drawn with seed 20261111: 670 drawn (530 core, 140 RAN5) and 667 admitted by the gate. By working group, the admitted items number 110 (RAN1), 140 (RAN2), 140 (RAN3), 139 (RAN4) and 138 (RAN5). They fall into seven families:

| Family | Items |
|---|---|
| `pack_lookup` | 100 |
| `pack_lookup_empty` | 86 |
| `disposition_pack` | 99 |
| `full_chain` | 100 |
| `revision_chain` | 82 |
| `clause_history` | 100 |
| `pack_origin` | 100 |

1. 581 items are answerable. The 86 `pack_lookup_empty` items expect an empty answer: 66 in the core set and 20 in RAN5.
2. Questions are generated from templates and name documents by identifier. The longest question has 315 characters.
3. Requested fields come from `cr_pack`, `tsg_meeting`, `disposition`, `wg_meeting`, `clause`, `final_document` and `document`.
4. The five-hop sets in `benchmark/headroom/` hold 297 admitted items of 300 drawn, in the families `clause_neighbours`, `first_change` and `previous_pack`.

**Abstention items.** 160 items: 60 in RAN3, 60 in RAN4 and 40 in RAN5. By class, 60 are `answer`, 60 `none` and 40 `insufficient`; the `insufficient` items are in RAN3 and RAN4.

**Stored responses.** `responses/` holds the responses of the conditions evaluated in the paper:

1. *Closed-book, dense retrieval (eight chunks), oracle evidence and oracle text only,* each with llama3.1:8b and qwen2.5:14b on a local GPU; dense retrieval embeds with bge-m3.
2. *Search agents* (Claude Opus 5.5): text search over passages that carry the record fields, the same over passages without them, raw-text search over the documents, and a dense retrieval tool.
3. *Text-to-SQL and Text-to-Cypher agents:* Claude Opus 5.5 runs, ten per language, and Codex CLI runs with the schema alone and with value domains or schema exploration, with the queries, their execution results and the repair round.
4. *Published-schema baseline* over the 3GPP CR database schema.
5. *Gold re-derivation rounds* by Claude Code subagents and the Codex CLI (`responses/chain_rederivation/`).

The result files of the audits and analyses that the paper reports (pack-link, clause-link, disposition and list-line audits, relational equivalence, text-route ceiling, substitution and schema ablations) sit at the top of `responses/` and in its subfolders.

**Labels.** The item builder computes the gold rows by walking the records forward from the anchor. The gate re-derives them by a different route: it loads the reverse-direction records (the members of each CR pack and the modifying change requests of each clause) into SQLite and runs one SQL query per family. It also recomputes the hash of every cited source file.

Disposition codes are assigned by explicit sentence rules over the body blocks of the meeting report, with tracked changes accepted. A source-verified disposition carries the report path and its SHA-256, a locator, the scope and the name of the rule that assigned the code.

**Relationships.**

| Link | Properties |
|---|---|
| Revision | `isRevisionOf`, `revisedTo` |
| Meeting | `presentedAt` |
| Pack membership | `belongsToCRPack`, `hasCR` |
| Clause modification | `modifiesSection`, `modifiedByCR` |
| Work item | `relatedTo` |
| Liaison routing between working groups | `sentTo`, `ccTo`, `originatedFrom`, `replyTo`, `originalLS`, `replyIn` |

**Splits.** The benchmark is an evaluation set. RAN5 is a separate partition and is scored apart from the core set.

**Quality measurements.** An automated audit re-opened 500 source-verified dispositions per working group, sampled with seed 20261111:

| WG | File hash matches | Every quoted fragment at the locator | Re-read code agrees (records with a decision line) |
|---|---|---|---|
| RAN1 | 500/500 | 496/500 | 214/248 |
| RAN2 | 500/500 | 500/500 | no decision line in the sample |
| RAN3 | 500/500 | 499/500 | 493/494 |
| RAN4 | 500/500 | 500/500 | 486/486 |
| RAN5 | 500/500 | 500/500 | 500/500 |

Two link audits, written apart from the build code, check each pack link against the pack cover sheet and each clause link against the change-request form. Their per-working-group results are in `responses/pack_link_audit.json` and `responses/clause_link_audit.json`.

**What runs on the released files.**

1. *Scoring.* Rescoring the stored responses with the released scorer reproduces 202 of the 206 entries of the 30 stored score reports, equal in every field except the response path. The other four entries belong to `responses/chain_eval/oracle_evidence/scores_dense_current_items.json`.
2. *Text-to-SQL.* `sqlite/` holds, byte for byte, the five databases of the query conditions; `SHA256SUMS.txt` gives their hashes.
3. *Item builder and gate.* `restore/check_benchmark.py` stages a clean copy of the released records and rebuilds each working group from its stored anchors, then runs the independent SQL gate and compares the drawn and admitted files byte for byte. The current preparation report is `sources/package_checks.json`.

The gate, the abstention checks and the disposition audit also read the meeting reports that `restore/restore_sources.py` fetches from the public 3GPP archive (Section 6).

**People in the data.** 3GPP documents name the delegates who submit them and the companies that source them. The package leaves out the following:

1. the contact and company record kinds, and the `hasContact` (539,132 TDoc records) and `submittedBy` (542,915 TDoc records) links to them;
2. 14 liaison link values that point to people: eight derived from an e-mail address (seven `replyTo`, one `sentTo`) and six that name a person (four `sentTo`, two `ccTo`);
3. 240 liaison link values that hold free text in place of an identifier (154 `originalLS`, 85 `replyTo`, one `replyIn`);
4. every text field copied from a 3GPP document: titles, abstracts, report sentences and quotes, cover-sheet fields and notes.

What remains in the records is identifiers, codes, dates, links between identifiers (TDoc numbers and working-group or organisation identifiers), archive paths, hashes and locators. Archive paths and member names stay as the 3GPP archive publishes them, and some of these file names carry title words, company names or a delegate's name.

In the stored responses and result files, values that repeat document text, a person's name or a company attribution are replaced by a marker with the SHA-256 and length of the original. The files in the root-level redaction lists list every changed file with the hash of its original and of the released copy and the count of each kind of marker.

## 3. Collection process

**Sources.** All inputs come from the public 3GPP file archive (https://www.3gpp.org/ftp):

1. working-group meeting reports;
2. TDoc lists (spreadsheets);
3. change-request documents and the cover sheets of plenary CR packs;
4. Technical Specifications.

The records cite each file by its archive path. `sources/manifest.jsonl` gives each cited meeting report its public archive URL and hashes.

**Mechanism.** The scripts in `code/`:

1. download the archive files;
2. bring each meeting report into Office Open XML: of the 276 cited reports, 211 are used as published, three `.docm` reports are repackaged as `.docx`, and 62 are converted with LibreOffice 7.3.7.2 in headless mode;
3. parse the files into body blocks, list rows and cover fields;
4. write the records.

Where a report entry and the document list describe the same document differently, the recorded identity review settles the difference, and its receipt is kept in `receipts/`.

**Who performed the work.** The checks are automated: scripts, and re-derivation rounds by Claude Code subagents (Claude Fable 5.2 and Claude Opus 5.5) and the Codex CLI.

**Timeframe.** Coverage is defined by the meeting ranges and releases in Section 2.

## 4. Preprocessing, cleaning and labeling

1. *Report text.* A report is read as body blocks with tracked changes accepted. A locator names either a half-open range of body blocks (`accepted body blocks [i,j)`) or a table block and row with the body blocks that govern it (`accepted table block t row r; governing body blocks [i,j)`).
2. *Disposition codes.* A named sentence rule assigns one of 16 codes. The record's `assessmentMethod` keeps the rule, the scope, the subject and the identity of the target document.
3. *Hashes.* Each hash is the SHA-256 of the cited file.
4. *Clause links.* These are read from the clauses-affected field of the change-request cover and resolved against the clause index of the specification at the change request's target release.
5. *Pack links.* These come from the cover sheet of each plenary CR pack and from the pack directory that holds each change request.
6. *Raw data.* The raw sources stay in the public 3GPP archive; the source manifest records the URLs and hashes of the cited meeting reports.

## 5. Uses

**Intended uses.**

1. Evaluating retrieval, retrieval-augmented generation, search agents, Text-to-SQL and Text-to-Cypher systems on multi-hop chain questions.
2. Evaluating abstention on empty-answer and insufficient-record questions.
3. Studying how source-bound records are built from meeting reports.

**Reading the answers.** A returned path states which documents the records connect: a working group recorded a decision on a document, the change request was listed in a plenary pack, and the change request names a clause. Such a path is a documentary trace. Assessing the technical influence of a contribution, or judging a person or company, calls for evidence beyond these records.

## 6. Distribution

**Access.** https://github.com/spectra-ontology/spec-trace

**License.** The package is under Creative Commons Attribution 4.0 (https://creativecommons.org/licenses/by/4.0/); see `LICENSE`.

**3GPP documents.** The package refers to 3GPP documents by identifier and archive path, and it cites meeting reports by archive path, SHA-256 and locator. `restore/restore_sources.py` restores the cited reports locally from the public 3GPP archive, and the restored files stay under the 3GPP terms (https://www.3gpp.org/about-us/legal-matters, https://www.3gpp.org/terms-of-use).

**Restoring the cited reports.** `sources/manifest.jsonl` lists 280 meeting reports: the 276 cited by source-verified dispositions, two cited only by pending dispositions, and two read by the abstention builder. For each report, the manifest records:

1. the cited path and the SHA-256 of the cited file;
2. the public archive URL, the alternate location in the archive's `Report/history/` folder where one exists, and the SHA-256 of the archive;
3. the archive member name and its SHA-256 (272 reports; the other eight are downloaded as files);
4. how the cited file is obtained from the member: used as published (211), repackaged from `.docm` (3), or converted with LibreOffice 7.3.7.2 (66), with the recorded input and output folders, the identifiers of embedded objects (16 reports) and the ZIP entry date.

The restore script downloads each archive, checks the archive hash and the member hash, rebuilds the cited file as recorded, checks it against the cited hash and writes it at its cited path. A full restore downloads 328 MB and matches all 280 reports on every check: archive hash 280/280, member hash 272/272 and cited-file hash 280/280.

## 7. Maintenance

**Maintainers.** The authors maintain the package through the issue tracker of the repository (https://github.com/spectra-ontology/spec-trace/issues).

**Versions.** Releases are tagged in the repository. Benchmark items are frozen within a release, and the question hash in each stored response ties it to its item.

**Contributions.** Corrections and new question families are proposed through the issue tracker and enter through the same gate as the released items.

**Evidence rehydration.** `sources/disposition_bindings.jsonl.gz` supplies text-free quote hashes, character counts, decision spans and source-field locators for all 358,062 dispositions. After restoring reports, `restore/restore_bindings.py` checks source hashes, restores the accepted source passage and emits a local quote only when its exact producer receipt matches. `restore/validate_bindings.py` validates the resulting JSON-LD with the packaged ontology and all 44 node shapes, with RDF 1.1 string representation normalization. The local preparation smoke check covers the first 20 dispositions of each WG: 100 exact passage matches, 100 direct rule agreements and SHACL conformance. This sample scope is distinct from the corpus-wide locator audit and target-identity reviews.

**Competency-query evidence.** `sources/competency_queries/index.json` indexes 25 sanitized original loaded-graph execution receipts (644 PASS, 10 NO_DATA) with original-file and projected-file hashes. The receipts retain outcome identifiers, counts, guard checks and project-authored queries, while the original answer samples and source-text fields remain in the original records. These stored execution outcomes describe the original loaded process graph; the benchmark gate independently checks the released query projection.

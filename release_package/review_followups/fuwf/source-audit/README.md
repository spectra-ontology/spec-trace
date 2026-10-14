# Fixed original-source machine audit

This local diagnostic is complete. It does not establish corpus accuracy,
full-corpus completeness, or domain-expert semantic validity. No files have
been published externally by this job.

The protocol, seed `SPECTRA-fUWF-source-audit-1`, and balanced selection rule
were fixed before comparison labels. Ten records per relation, direction and
working group were requested, without replacement. The original-source
REFERENCES frame in RAN5 contained only one eligible passage: 491 cases were
selected for 500 requested slots. REFERENCES source-first therefore has 41
selected records and nine unavailable frame slots; every other stratum has
50 selected records. Missing originals, legacy DOC unreadability, nonunique
identities and insufficient provenance remain unresolved.

| Relation | Direction | Selected / requested | Machine set match | Machine set difference | Unresolved |
|---|---|---:|---:|---:|---:|
| MODIFIES_SECTION | graph-first | 50 / 50 | 4 | 0 | 46 |
| MODIFIES_SECTION | source-first | 50 / 50 | 7 | 16 | 27 |
| REFERENCES | graph-first | 50 / 50 | 4 | 0 | 46 |
| REFERENCES | source-first | 41 / 50 | 6 | 0 | 35 |
| MADE_AT | graph-first | 50 / 50 | 9 | 0 | 41 |
| MADE_AT | source-first | 50 / 50 | 4 | 0 | 46 |
| RESOLUTION_BELONGS_TO | graph-first | 50 / 50 | 0 | 1 candidate difference | 49 |
| RESOLUTION_BELONGS_TO | source-first | 50 / 50 | 0 | 1 candidate difference | 49 |
| SENT_TO | graph-first | 50 / 50 | 33 | 0 | 17 |
| SENT_TO | source-first | 50 / 50 | 37 | 0 | 13 |

These labels compare complete sampled original fields or matched paragraph
spans against all frozen target edges of a selected record. REFERENCES
matches citation identifier tokens only: every reference meaning remains
unadjudicated. MADE_AT matches original report occurrences and keeps multiple
meeting identities unresolved. Agenda labels use the closest explicit
numbered heading as a machine candidate; the two candidate differences are
not verified errors in graph agenda relationships. Lexical supportive or
contextual cues do not provide semantic gold labels. No confidence interval
or population accuracy estimate is reported.

Source-first CR set differences need edition/snapshot scope reconciliation
before interpreting them as missing eligible graph relationships. For
example, native ZIP member R2-2505094 contains `Clauses affected: 2, 6.5.2.2,
6.5.2.13` for 37.355 / Rel-19, while its matched frozen record has no
MODIFIES_SECTION targets. The artifact retains the exact native ZIP/member,
hash, cover-cell locator, source target set and empty graph target set.

Original native DOCX bytes are authenticated against downloaded ZIP members.
Converted retained DOCX without exact native ZIP byte identity is unresolved.
Legacy DOC members were not converted by this reader. LS inputs are native
retained XLSX cells with workbook hashes, sheet/row locators and the original
To text; they are explicitly distinguished from ZIP-authenticated DOCX.
Production parsing JSON and the operational graph database are never used
as source truth. Separate root-agent legacy-DOC/recipient extensions are not
included in this table.

The source-first LS pool has all 50 fixed original rows in `sampling.json`.
`results.json` and `evidence.jsonl` preserve source-only normalized recipient
sets independently of graph availability. A matched-information routing
diagnostic built from this pool must state its own source-only scope; it is
not an evaluation of the original 624 benchmark questions or KG superiority.

## Reproducibility and correction history

- `protocol.json`: predeclared source/graph frames, no-replacement rule and limits.
- `sampling.json`: fixed identities, selection ranks, source-input pins and frozen TTL SHA256 values.
- `sampling_producer.py`: byte-exact code used to select the sample.
- `results.json`: final canonical comparisons, input hashes, status counts and all cases.
- `evidence.jsonl`: exact quotes, original paragraph windows, locators and provenance for every selected case.
- `guard-prepare/`: successful bounded sampling execution.
- `guard-audit/`: owned initial cache attempt stopped because MemoryHigh reclaim stalled; no labels exported.
- `guard-audit-streaming/`: initial successful streaming reader execution.
- `initial-reader-output/`: byte-preserved initial reader/results/evidence and correction notice. Initial mismatch labels must not be used as graph error counts.
- `guard-audit-canonical-uri/`: successful final same-sample original-source rerun after canonical URI correction.

The initial comparison mistakenly included `section/` only on source clause
keys and compared meeting suffix case (`101Bis` versus `101bis`) literally.
The final reader removes the optional section namespace component and uses
meeting-label casefold. It preserves numeric identifiers, suffixes and
hyphens, so `100` and `100-e` remain distinct. All 491 case identities,
selection ranks, source-field scopes and semantic-adjudication criteria are
unchanged. Source/graph set differences remaining after normalization are
retained.

- Sampling producer SHA256: `68a6056564b69ba1e2e9ae21c3a603ae5a8868c693f4656219b4ce0aee232443`.
- Initial streaming reader SHA256: `dd8709a77c4ab6ee567b6311da304fdd6320faba756df003ca686f496e5d3480`.
- Final canonical reader SHA256: `2f9464406bfd45c8ee34d50e13a74997182cb3c6b4c095539e310d81a6b377f5`.
- Fixed sampling SHA256: `058d5f76c4039d12e9f62b96523eb3a2f51c2263ccc261ad95342eb8a3ae7413`.
- Protocol SHA256: `727580b8bf122fc18972667f1fe93e9356c55469131e76974f8abefb4770c443`.

The final rerun exited 0 in 317.110 seconds with `INPUTS_UNCHANGED` and no
input drift paths. The unchanged existing guard enforced MemoryMax=2GiB,
MemoryHigh=1GiB, swap=0, tasks=64, CPU affinity 0/1, nice=19, and fresh Windows
and WSL memory reserves of 16GiB. Recorded peak cgroup memory was 1,074,003,968
bytes; OOM/max/swap events were zero. Model calls, database calls and
domain-expert validations were zero. Frozen TTL, native originals,
production parsing, public repository and other research tracks were not
modified.

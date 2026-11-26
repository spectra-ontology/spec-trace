# Decision codes and released frequencies

SPECTRA stores sixteen disposition codes for decisions about a target document. The formal closed set is the `dispositionCode` property of `DecisionDispositionShape` in the [published SHACL shapes](../docs/spectra-shapes.ttl). The original [reading codebook](../studies/disposition_reading/codebook.md#codes) defines each code and the three outcome scopes.

The [scope mapping](scope_mapping.md) connects the ontology, native graph, SQLite column and verification evidence.

The codebook also supplies `cannot_tell` as an auxiliary reader assessment when a packet provides insufficient evidence to decide. Stored dispositions use the sixteen formal codes below; `ambiguous` is a stored code for a passage whose outcome cannot be assigned to the target.

## Complete record census

The census counts all 358,062 released phase-2 `DecisionDisposition` records across five working groups, including every evidence status and scope. Counts describe the released records; the manuscript reports source checks and reader assessments separately. All sixteen formal codes occur in the combined population. A `0` denotes zero observed records of that code in the named working group.

| Code | RAN1 | RAN2 | RAN3 | RAN4 | RAN5 | Total |
|---|---:|---:|---:|---:|---:|---:|
| `agreed` | 6,036 | 14,484 | 7,348 | 37,441 | 34,255 | 99,564 |
| `withdrawn` | 109 | 342 | 1,620 | 8,373 | 5,703 | 16,147 |
| `rejected` | 0 | 3 | 70 | 2 | 2 | 77 |
| `not_agreed` | 1 | 263 | 2 | 0 | 1 | 267 |
| `not_pursued` | 65 | 1,795 | 395 | 2,408 | 96 | 4,759 |
| `not_treated` | 122 | 910 | 16,876 | 2,868 | 875 | 21,651 |
| `merged` | 1 | 57 | 332 | 1,444 | 0 | 1,834 |
| `not_concluded` | 0 | 0 | 57 | 60 | 0 | 117 |
| `replied_to` | 0 | 0 | 31 | 7 | 0 | 38 |
| `noted` | 4,626 | 8,646 | 18,142 | 67,500 | 5,492 | 104,406 |
| `postponed` | 10 | 806 | 169 | 2,875 | 2 | 3,862 |
| `revised` | 198 | 6,251 | 10,047 | 24,372 | 18,793 | 59,661 |
| `endorsed` | 1,824 | 1,124 | 3,049 | 13,464 | 165 | 19,626 |
| `conditionally_agreed` | 33 | 905 | 2 | 0 | 3 | 943 |
| `partially_agreed` | 412 | 129 | 21 | 10 | 15 | 587 |
| `ambiguous` | 9,212 | 11,521 | 351 | 3,352 | 87 | 24,523 |
| **Total** | **22,649** | **47,236** | **58,512** | **164,176** | **65,489** | **358,062** |

## Recount and source bindings

The [machine-readable counts](decision_code_counts.json) include the SHA-256 of the formal shapes, original codebook, all five input files and the [stdlib-only recount script](recount_decision_codes.py). Input files are `records/phase-2/RAN1/decision_dispositions.jsonld` and the corresponding `.jsonld.gz` files for RAN2 through RAN5. The script reads the formal code set from the named shape, checks the codebook vocabulary, includes zero-count cells and rejects any stored code outside that set.

From the package root:

```sh
python3 -B ontology/recount_decision_codes.py --release . --expect-total 358062 --out work/decision_code_counts.json
```

The generated JSON reproduces `ontology/decision_code_counts.json` byte for byte from the same packaged inputs.

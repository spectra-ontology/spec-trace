# Source-label sensitivity for full-chain questions

The released gold projects 396 stored CR-to-section links to clause labels
across 100 full-chain items. The checked affected-clause fields name every
one of those labels. For 97 items the explicit sets agree exactly. Three
forms list four additional labels. Three other forms contain four placeholder
tokens, such as `5.1.x`.

| CR | Additional cover labels | What the source and snapshot show |
|---|---|---|
| R3-255996 | `9.3.3.A`, `9.3.3.B` | The CR introduces those headings. The same titles appear at `9.3.3.67` and `9.3.3.68` in TS 38.413 V19.2.0. |
| R4-2219117 | `5.3.2.4` | The label appears in the cover field. The matching-specification snapshot has no section at that label. |
| R5-263126 | `5.2.A.2` | The CR body and TS section record use `5.2A.2`. The CR's stored section-change links do not include that label. |

The receipt identifies every source by its official archive URL, archive hash,
and ordered member selectors. The CR field is the accepted text of
`Clauses affected` in `word/document.xml`. For R3-255996 the corresponding
final titles can be read on page 386 of
[ETSI TS 138 413 V19.2.0](https://www.etsi.org/deliver/etsi_ts/138400_138499/138413/19.02.00_60/ts_138413v190200p.pdf).
The native evidence is
[3GPP TS 38.413 V19.2.0](https://www.3gpp.org/ftp/Specs/archive/38_series/38.413/38413-j20.zip),
`38413-j20.docx`, at zero-based paragraph indices 26799 and 26844 in
`word/document.xml` (DOCX SHA-256
`8f65a175c09e3970edb9794d01341de94f99dc9e4b11523c2569129c61a129bd`).
[The native and reconstructed source checks](../../../restore/source_links/README.md)
describe the archive and conversion bindings.

## Comparison and rescoring

The audit enumerates labels from the pinned form field before it compares
them with the projected gold. It ignores document, specification, edition
and ASN.1 mentions in the field. The primary reading preserves printed
clause spelling, ignores case, and separates placeholder suffixes `x` or
`xx` from concrete labels. Parent and child labels count separately. The
consolidated CR R4-2215213 includes attribution to multiple constituent
CRs. The audit counts actual clause tokens in that field and skips the
attributed document IDs and specification numbers. No field required range,
slash-shorthand or table-number adjudication.

The sensitivity crosses each alternative clause-label set with the original
four-field prefix set. The published identity scorer then applies the same
meeting aliases, field order, question hashes and exact row-set comparison to
the same saved answers. The historical benchmark continues to use the
released snapshot. The alternate labels intentionally follow the cover
wording, including the extra dot in R5-263126.

| Historical interface | Released projections | Explicit cover labels |
|---|---:|---:|
| Raw text, 2 runs | 182 / 200 (91.0%) | 187 / 200 (93.5%) |
| Record chunks, 3 runs | 291 / 300 (97.0%) | 299 / 300 (99.7%) |
| Record bodies, 3 runs | 61 / 300 (20.3%) | 64 / 300 (21.3%) |
| Dense tool, 2 runs | 192 / 200 (96.0%) | 198 / 200 (99.0%) |
| Dense tool with cap, 1 run | 73 / 100 (73.0%) | 75 / 100 (75.0%) |
| Opus SQL, 10 runs | 931 / 1000 (93.1%) | 903 / 1000 (90.3%) |
| Opus Cypher, 10 runs | 960 / 1000 (96.0%) | 932 / 1000 (93.2%) |

The item and run detail covers all 37 stored conditions. It also tests two
distinct alternatives. Including placeholder strings verbatim changes raw
text to 193/200. Restricting the released section links to the form's own
edition removes 15 labels across 11 items and changes raw text to 161/200.
These are separate comparisons against the same original answer rows.

## Replay from the release root

The shipped receipt contains derived labels, hashes, source locators, and
per-item score changes. The score replay requires Python 3.10 or later and
NumPy. It rebuilds all three alternatives from the label sets and verifies
archived response hashes and exact counts.

```sh
mkdir -p work
python3 -B benchmark/task_exposure/full_chain/audit_full_chain_source_labels.py \
  --release . \
  --label-receipt benchmark/task_exposure/full_chain/full_chain_source_labels.json \
  --out work/full_chain_score_replay.json
```

The replay reads the packaged benchmark, scorer, response files and SQLite
snapshots. Fresh form extraction is a separate path. In the original project
checkout with pinned corpus and archived SQLite paths present, run the same
command with `--checkout /path/to/spectra` in place of `--label-receipt ...`.
That path reads all 100 form fields again after verifying the source and
archive hashes. Neither replay calls a model.

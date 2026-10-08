# SPECTRA: the 3GPP RAN standardization-process dataset

SPECTRA organizes public contributions, meeting decisions, change requests and
specification structure across the five RAN working groups. The released graph
snapshot contains 966,859 nodes and 4,908,850 relationships. SpectraCQ contains
624 released questions with executable reference queries and graph-derived answer
sets, from 654 authored questions. See the [counts manifest](release_package/MANIFEST.md)
for the per-group totals and the distinction between graph replay and question validity.

## Start here

- [Evaluation scopes and evidence](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md): how the current analyses relate to the original benchmark.
- [Release package](release_package/README.md): ontology, schema, examples, pipeline and known data-quality issues.
- [Historical benchmark and scoring](release_package/cqs/spectra_cq_v2.0/README.md) and [baseline records](paper/baseline/README.md).
- [Reproduction commands](release_package/tests/README.md) and [artifact walkthrough](release_package/ARTIFACT.md).

## Evaluation evidence

| Analysis | What it evaluates | Scope |
| --- | --- | --- |
| [31 original questions](release_package/cqs/contract_repair_v1/original_source_aligned/README.md) | Retained predictions on unchanged questions admitted by two AI contract checks and complete saved reference execution | Nine models, legacy answer-column scoring; no multihop item or independent expert validation |
| [36 formal task variants](release_package/cqs/contract_repair_v1/matched_retrieval_measurement/README.md) | Explicit named-field, typed complete-record scoring of single-pass text, two-round text and generated Cypher | Separate tasks; unequal graph/text access and unverified source-cutoff equivalence |
| [Core 560 and historical subsets](paper/baseline/README.md) | Original scores, whole-row sensitivity and retained SQL/Cypher reanalysis | The complete original question/scoring contract remains unfinished |

The historical 45-question diagnostic and the current 31-question diagnostic use
different criteria; they overlap on 15 IDs and neither contains the other. The
36 variants share no original-question IDs with the 31. Their scores must remain
separate. AI checks and query-derived answers do not provide independent expert
validation. Missing-information abstention and transfer outside RAN remain untested.

The [scope guide](release_package/cqs/contract_repair_v1/README_evaluation_scopes.md)
also distinguishes graph Section structure from retained text excerpts, direct
links from contextual joins, liaison-count populations, historical Table 14
results from later replays, and text-body passage limits from metadata.

## Get the data

The Git repository includes the ontology, benchmark, metadata-only process graphs,
construction code and retained evaluation inputs and outputs. The five larger
`RAN{1..5}-body.ttl` graphs are distributed separately in the
[archived release](https://doi.org/10.5281/zenodo.21504833), version 2.0.0.
The [body-graph inventory](release_package/kg/per_wg/README.md) explains placement,
counts and known data-quality issues. The full text-ranking corpus is not deposited.

The [concept DOI](https://doi.org/10.5281/zenodo.20034871) locates the latest
archived version. Later Git additions are separate from those frozen archives;
cite the Git commit used for an evaluation. The ontology is version 1.1.1;
its persistent identifier is [w3id.org/spectra](https://w3id.org/spectra).

## Reproduce from a Git checkout

Run from the repository root. The release checks need `rdflib` and `pyshacl`;
the two retained-score replays below need only Python 3.10 or later.

```bash
pip install rdflib pyshacl
python3 -B release_package/tests/verify_benchmark.py --quick --out /tmp/spectra-quick-check

python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813

python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-strict-record-replay.json
```

The quick gate checks the Git-only release without a database. Five additional
checks require the body-graph deposit. The score replays read retained outputs;
they make no model or database calls and do not reproduce the full text-ranking
stage. Use a new output filename for the strict-record replay, which refuses to
overwrite an existing report. Full graph replay requires a scratch database;
follow the [test guide](release_package/tests/README.md) before running it.

## Citation and license

Use [CITATION.cff](release_package/CITATION.cff),
[CodeMeta](release_package/codemeta.json) or the
[SpectraCQ citation](release_package/cqs/spectra_cq_v2.0/citation.bib).
SPECTRA-authored components are licensed under CC BY 4.0. 3GPP-derived text
retains separate source attribution and is not relicensed as SPECTRA-authored
content; see the [package license](release_package/LICENSE).

Maintainer: Sihyeon Choi, Samsung Electronics. Questions and corrections:
[repository issues](https://github.com/spectra-ontology/spec-trace/issues).

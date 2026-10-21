# NR-U study-to-section source-role diagnostic

SPECTRA links study identities, implementation records and release-aware section
identities into a reproducible source-role audit. This artifact preserves the
original question and the exact source evidence used for its frozen-input
classification: `unsupported_frozen_data` / `new_section_role_and_identity_not_retained`.

Original question: **Which new sections did the NR-U study (TR 38.889) add to
TS 38.211-38.214? (PHY-layer reference)**

Run with Python standard library from any copied directory:

```sh
python3 -B -I reproduce.py
```

The replay opens seven original document XML/style pairs, follows the preserved
query through an independent SQL translation and checks all four study impacts.
The single resolved Section16 identity is TS38.213's sidelink chapter. The NR-U
implementation CR for TS38.212 explicitly marks six new clauses in its original
cover page and inserted headings; the frozen CR retains eleven modified-section
links while the six source-specific new-clause roles require source enrichment.
The source and target identities, original author context and alternative CR
traversal are preserved together for examination.

The bounded graph slice and actual whole-frozen audit receipts have distinct
roles. Offline replay checks the included source bytes and saved finite evidence.
The supplied provenance recipe accepts an explicit original SQLite and repository
root to repeat the original-input audit. Human expert reviews:0; AI reviews are
nonblind. This classification contributes evidence to original560 accounting;
admitted task and model-evaluation totals remain their independently measured
sets. Original questions and source-enriched experiments retain separate inputs.

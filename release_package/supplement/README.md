# SPECTRA Supplementary Materials

These files are companion to the accompanying paper (currently under
review). They were trimmed from the paper body to comply with the venue
page limit. The content is preserved here verbatim and is
also reproducible from the artifacts elsewhere in `release_package/`.

## Contents

| File | Purpose |
|---|---|
| `PAPER_APPENDIX.tex` | Appendix A--G content (TTL/SHACL excerpts, SPARQL listings, per-WG class coverage table, regression cases, reproducibility checklist, artifact treatment, process-KG data quality) plus the E6 LLM evaluation pilot. Source of truth. |
| `LLM_EVAL_PILOT.tex` | Earlier-draft LLM eval text (now folded into `PAPER_APPENDIX.tex` §E6); kept for diff history. |
| `standalone_appendix.tex` | Wrapper providing LNCS preamble + title + main-paper label stubs so `PAPER_APPENDIX.tex` compiles as an independent submission PDF. |
| `build_supplement_pdf.sh` | One-shot build: runs `pdflatex` twice and copies `standalone_appendix.pdf` to the user's Desktop as `SPECTRA_Supplementary_Appendix.pdf`. |

Reproducible from: `ontology/spectra.ttl`, `shapes/spectra-core.shacl.ttl`, `cqs/spectra_cq_v2.0/cypher/`, `validation/per_wg_class_coverage.json`, `validation/validation_manifest.md`.

## How to render

```bash
# Standalone PDF for supplementary submission:
cd release_package/supplement
./build_supplement_pdf.sh
# → standalone_appendix.pdf (here) + ~/Desktop/SPECTRA_Supplementary_Appendix.pdf

# Or include into the paper LaTeX source as
# \input{release_package/supplement/PAPER_APPENDIX.tex}
# (in which case main-paper \ref{sec:eval} etc resolve naturally).
```

## Why these moved out of the paper body

The submission venue's page budget counts appendix material toward the
page limit. To keep the paper body self-contained within that limit, the
appendix material was relocated here while remaining part of the release
package.

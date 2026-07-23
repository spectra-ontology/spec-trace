# Chart Parser Fidelity Note (RAN1 Chart=1)

**Context.** The released `ran1_instance_counts.json` reports `Chart: 1` for the
RAN1 instantiation. The single-instance count is real, parser-derived, and not
noise — this note records the supporting evidence so reviewers and downstream
maintainers can verify the parser's behaviour.

## What the parser does

`scripts/RAN/formal/RAN1/phase-2/report-parser/chart_extractor.py` walks every DOCX Final
Report and distinguishes two embedded-content cases inside `w:drawing`:

| Element                     | SPECTRA class | Rationale                                                  |
|-----------------------------|---------------|------------------------------------------------------------|
| `<a:blip>` (raster image)   | `Figure`      | Author pasted/screenshotted a plot                         |
| `<c:chart r:id="rIdN">` only| `Chart`       | Author embedded a native OpenXML chart (Excel-linked data) |

`Chart` is reserved for the second case: structured chart data (axes, series,
data points) carried inside the DOCX, not a rasterized picture. The release
ships `Figure=120` and `Chart=1` for RAN1 — the parser correctly attributes
each embedded drawing to the matching subtype.

## The single RAN1 Chart instance (CHT-114b-001)

Source meeting: **RAN1#114b** (Toulouse, 2023-08; AI/ML for air interface,
Rel-18 Work Item).

Parsed metadata (from `ontology/output/RAN/formal/parsed_reports/RAN1/RAN1_114b.json`):

```json
{
  "chart_id": "CHT-114b-001",
  "caption": "Figure 6.3.2: 1",
  "chart_path": ".../charts/RAN1_114b/CHT-114b-001.xml",
  "chart_type": "scatterChart",
  "chart_number": "6.3.2"
}
```

Chart payload (`ontology/output/RAN/formal/charts/RAN1/RAN1_114b/CHT-114b-001.xml`,
~19 KB OOXML):

- **Type:** `scatterChart` on log–log axes
- **Title:** `Model complexity`
- **X axis:** `model parameter (M)` — Excel range `Sheet1!$C$6:$C$34` etc.
- **Y axis:** `Computational complexity Flops(M)` — `Sheet1!$E$6:$E$34` etc.
- **Series (4):** `BM-Case1 Tx beam`, `BM-Case1 beam pair`, `BM-Case2 Tx beam`,
  `BM-Case 2 beam pair`
- **Domain:** beam-management AI/ML model complexity comparison

The contributing company chose to insert a native Excel chart (not a raster
screenshot), which is rare by 3GPP authoring convention; this is the only such
case the parser found across 60 RAN1 Final Reports.

## Why we keep `Chart=1` in the release

1. **Parser fidelity.** The single hit is direct evidence that the parser
   discriminates native OpenXML charts from raster figures rather than
   collapsing them. Removing the count would hide that capability.
2. **Schema completeness.** `spectra:Chart` is a first-class auxiliary-content
   class in the SPECTRA ontology; per-class counts are reported as observed.
3. **Reproducibility.** Reviewers can re-derive the count by re-running
   `chart_extractor.py` over the released DOCX corpus and the bundled chart
   XML.

## Where the count appears

- `release_package/validation/ran1_instance_counts.json` (`RAN1.counts.Chart`)
- Paper Table 6 (per-class counts), with a footnote pointing to this note
- Schema TBox: `release_package/ontology/spectra.ttl` — class `spectra:Chart`
  with object property `containedIn` (Meeting) and data properties
  `chartId`, `chartPath`, `chartType`

The count is intentionally retained as parser-fidelity evidence; do not
zero-out or remove the `Chart` key without re-running the extractor on the
current corpus and updating this note.

# Bounded boundary and equation diagnostics

This package reproduces two concrete failures. A candidate boundary at a tabbed Draft-CR paragraph would discard its own subsequent Final-CR approval. An empty MTEF script following a space makes the current renderer synthesize `( )`; a separate local proposal removes this artifact while preserving actual empty fences.

Run with Python 3.10+ and its standard library:

```sh
python3 -B -I verify_diagnostics.py
```

Default replay reads only included files: six XML contexts,157 exact original OLE/WMF members for93 object occurrences, byte-pinned decoder code, a helper excerpt, and5 AST controls. It checks the old and prospective readings. It does not rerun the full3176-record scan or LibreOffice rendering. Optional original DOCX verification, after independently obtaining the source listed in `provenance.json`:

```sh
python3 -B -I verify_diagnostics.py --source-docx-123 /path/to/Final_Minutes_report_RAN1#123_v100.docx --source-docx-117 /path/to/Draft_Minutes_report_RAN1#117_v030.docx
```

The full DOCX hashes and exact archive/member locators are preserved. No original is downloaded automatically; missing optional inputs fail. Some windows include neighboring source material deliberately, because the boundary rule itself is under test. Four of five previously observed foreign spans had already been excluded in the original graph; they are not four new frozen-graph errors.

No patch is installed, no records are dropped, and no gold answer, original benchmark admission, paid model result or public graph changes. DCI remains pending. Neither native/preview agreement nor the one ROOT-AI visual observation certifies all93 formulas, original Word rendering, all31 required DCI contents or a generic segmentation policy. Human expert evaluations:0.

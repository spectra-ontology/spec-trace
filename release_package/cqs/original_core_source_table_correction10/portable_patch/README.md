This is a separate source correction for TS 38.133 section 9.2.5.1. It adds ten source-authored tables omitted by the released style-based extraction, using the existing TSTable class and the existing exact-edition Section owners. The frozen CQ1-5 result has 70 records and is preserved; the separate corrected source query has 80 caption records, comprising 62 actual Word tables and 18 authored Void captions. Every new record is an actual Word table.

The package contains ten exact DOCX member byte streams from five original standard archives, original archive/member hashes and CRCs, caption/table XML, the 140-triple additive delta, ten node mappings, AI semantic/source reviews and the completed native/SQL/23-control evidence. Historical evidence JSON preserves original execution paths. The executable manifest and reconstruction inputs use package-relative paths. Expert validation is zero. Query observations are evidence, not a replacement frozen gold or a model-performance claim.

Verify portable source bytes and all 80 caption/owner units with Python 3:

    python verify_rebuild.py

To reconstruct a separate RDF and relational snapshot, supply the exact baseline files identified in manifest.json and an unused output directory:

    python verify_rebuild.py --baseline-sql /path/to/RAN4.sqlite --baseline-rdf /path/to/RAN4-body.ttl --output /path/to/new-output

The script rejects mismatched baseline hashes, refuses output overwrite, preserves every old column and row in all 80 baseline SQL tables and checks the exact RDF prefix by baseline hash. It starts no database server and makes no network or model calls. The full baseline and reconstructed RDF/SQLite files are deliberately not shipped in this small patch package. No benchmark index, frozen question text or frozen gold file is edited. Publication and evaluation registration remain separate actions.

The evaluation directory holds a standalone, source-variant task and native-derived requested-field reference under the unchanged question and repair identity. It is separate from the frozen 70-record task. Actual source/native/scorer validation is complete; root registration and fresh model evaluation remain pending. Replay 23 meaningful identity/scope controls:

    python evaluation/verify_controls.py

Score a supplied prediction file, whose id and repair_sha256 must match this source-variant task:

    python evaluation/score_predictions.py --predictions /path/to/predictions.jsonl

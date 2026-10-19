# Four source-omission witnesses for the RAN2 FFS question

This is a diagnostic supplement for `RAN2_P2_CQ2-6`. Four passages in the original RAN2#132 report have their own **Agreements** heading and an active literal `FFS` marker. Their complete FFS-bearing sentences are absent from the preserved 3,413 Agreement `content` and `note` records after whitespace normalization, including a case-insensitive check.

Run the self-contained, standard-library replay from any directory:

```sh
python3 -B -I /path/to/this/supplement/verify_diagnostic.py
```

The replay opens the included original ZIP, verifies its member inventory and DOCX/XML/styles pins, checks the four original heading/body neighborhoods and run formatting, and repeats the exact-sentence absence search over all 3,413 preserved records. It rejects extra files, modified evidence and symlinks, including a symlink in the entry or an ancestor path. It uses no network, database, model, original workspace or large graph artifact.

The included archive came from the [official 3GPP report directory](https://www.3gpp.org/ftp/tsg_ran/WG2_RL2/TSGR2_132/Report/R2-2600002.zip). A separately saved HTTP 200 receipt records a byte-identical download; offline replay verifies the saved bytes without repeating that request.

This supplement establishes four source-versus-record witnesses. It does not establish every possible semantic paraphrase is absent, the complete Agreement population, current unresolved status, answer identities, top-ten membership, a graph repair, model performance or an additional admitted original question. Eight other unaligned source candidates and paragraphs outside the old candidate intervals remain unreviewed here. The original 560-question disposition is unchanged, with zero expert validations.

Paragraph indices use the original table-aware flattened paragraph order. They are not raw `w:body` child offsets; physical XML sibling paths are provided separately. `paragraph_XML_sha256` hashes ElementTree's default ASCII serialization; the embedded Unicode XML string has a different byte representation when it contains non-ASCII characters. The verifier compares parsed XML and recomputes the documented ASCII serialization.

The original query and English question are retained in `contract/original_question.json`. Prior candidate alignment is diagnostic metadata; it is not a completed source-recall proof. Reviews attached here concern these four source roles and the limits of the diagnostic, not a full seven-unit pass for the original question. Source bytes, frozen records and model results are not repaired by this supplement.

# Experimental interfaces and inputs

The paper evaluates a source-bound record resource through several interfaces.
The table below distinguishes the information given to a solver from the
inputs used by a diagnostic. All conditions use their recorded question and
scoring versions; stored responses remain the basis of the offline score replay.

| Condition or measurement | Input and attached fields | Execution and evidence |
|---|---|---|
| Closed-book local readers | Question and requested answer format | Two recorded local readers. Scores replay from released responses. |
| Dense local readers | Top eight bge-m3 chunks from the WG's resolution, CR and TDoc collections; each chunk's first 1,500 characters plus document, meeting, pack, clause and resolution metadata where present | The original retrieval corpus and embeddings determine the context. The portable replay checks all 1,334 recorded requests for the 667 admitted items against restored indexes; fresh retrieval retains its own vector-store and model requirements. |
| Oracle local readers | Chunks from documents cited by the gold, with a separate text-only variant | A reading diagnostic with selected evidence. This input is separate from end-to-end search. |
| Record-chunk BM25 agent | Search over the same record chunks, with their attached metadata | Three recorded Opus runs; one agent per third of each WG's questions in each run. |
| Text-only BM25 agent | Chunk body and own-document matches; record-built pack, plenary and resolution fields are omitted | Three recorded Opus runs. Uses its stated interface rather than the full record-metadata interface. |
| Raw-text BM25 agent | The documents' own text, including plenary documents, using the original WG and plenary indexes | Two recorded Opus runs. Raw-body transformation and original chunk identities are part of the input definition. |
| Capped dense-tool agent | bge-m3 retrieval over record chunks, at most 61 chunks per call | One recorded Opus run. The uncapped auxiliary runs retain their separate recorded scope. |
| Opus query writers | One WG's questions, requested fields and SQL or Cypher schema | Ten runs per language, A–J; first execution, read-only, with a 60-second cap. The released record projection supplies the query data. |
| Codex query writers | Schema alone; schema plus stored-value domains; or schema with a read-only query tool | Three distinct input conditions per language. The domain representation and exploration observations are retained with their packets and responses. |
| Retrieval containment | A specified retrieval route and its returned metadata/body fields, compared with gold answer fields | A literal-containment diagnostic. Gold fields are used for this diagnostic, rather than supplied to the search agent. |
| Engine and plan comparisons | The released relation projection or loaded graph, stored query text, recorded engine release, cap and plan | These measurements preserve their engine environment. Table replay recomputes scores and uncertainty from stored responses. |
| Source and link audits | Report passages, CR forms, pack covers, source inventories and structural resolver inputs | Report rehydration and the 604-pair CR check have executable instructions and stated validation scopes. Full-corpus audits additionally consume their original corpus inventories. |
| Synthetic contract stress | Disposable copies of released SQL data, fixed anchors and stored SQL | The separate SQLite 3.37.2 workflow tests marked synthetic perturbations and preserves original gold and responses. |
| Disposition-stage rebuild | Prepared text and existing links | The measured stage reconstructs dispositions. Source acquisition and the rest of the process graph have their own construction steps. |

## Reproduction status

The released offline command verifies the package and reproduces 60 historical
score entries and all 37 current analysis conditions, including both scoring
rules and their bootstraps. Report restoration, benchmark reconstruction,
source-link checking and synthetic stress have separate commands in
[REPRODUCING.md](REPRODUCING.md).

The [retrieval restoration workflow](restore/retrieval/README.md) supplies
text-free frontiers, source locators and executable reconstruction for the five
WG indexes and the plenary index. The preparation checks rebuilt all 4,753,237
WG record chunks from the original parsed-source tree. Plenary extraction
checked all 31,023 source files and 672,580 chunks against their recorded digests
before assembling the index. Acquisition, conversion, parsing and index
assembly each have their own receipts, so a fresh-download pilot and a complete
local-source reconstruction retain their respective scopes.

The [lexical diagnostic](restore/lexical_containment/README.md) reproduces
8,004 route records for the 667 admitted items. The
[dense-context replay](restore/dense_retrieval/README.md) reconstructs the
recorded top-eight contexts from the restored indexes and checks their request
digests. The released relation databases support SQL and graph-query
measurements; the retrieval frontiers reconstruct the separate text-search
interfaces.

The [corpus-audit workflow](restore/census/README.md) releases the source
inventory, metadata and reader/resolver dependencies. The whole-corpus audit
was rerun with the original local source tree and checked against the recorded
scientific outputs. Fresh source acquisition and native-document conversion
have separate, explicitly enumerated pilot receipts. Downloaded source text and
converted documents remain in the user's local workspace.

For an extension, retain the item IDs, interface, attached fields, search budget,
engine release and timeout with the new responses. The stored response replay
provides the scoring and aggregation reference.

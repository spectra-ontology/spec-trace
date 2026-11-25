# Shipped code

The package contains 519 code-manifest entries, with repository-relative paths and file-level provenance. [code_manifest.json](code_manifest.json) records each source, destination, byte count, SHA-256 and path-rewrite state.

| Group | Files |
|---|---:|
| analysis result files | 44 |
| analysis scripts | 24 |
| census restoration | 5 |
| credentials stub | 1 |
| imported repository modules | 35 |
| repository modules loaded by file path | 10 |
| retrieval restoration | 274 |
| tools scripts | 4 |
| track scripts | 121 |
| workload inventory | 1 |

The credentials module is the released stub. Construction, search replay, fixed-context reconstruction and scoring execute locally. The source reconstruction runtime is listed in [requirements-retrieval.txt](requirements-retrieval.txt); offline score analysis uses [requirements-replay.txt](requirements-replay.txt). Historical engine and plotting scripts retain their additional Neo4j, RDF and plotting dependencies.

## Verification

[The code-validation receipt](sources/code_validation.json) checks every listed file hash and size, compiles 468 packaged Python files and 34 restoration helpers in memory, and parses 7 shell files with `bash -n`. It also checks local Markdown file targets. These checks cover syntax and packaging. [REPRODUCING.md](REPRODUCING.md) links the separately executed construction, source-reading, retrieval and score-replay workflows. Earlier preparation evidence remains in `sources/package_checks.json` with its recorded scope.

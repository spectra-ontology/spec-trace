This directory audits retained experiment artifacts offline. It is outside the
frozen runtime code, databases, scorer, schema cards and model-input pipeline.
The tools in this audit directory never invoke a model, retry a scientific
request, access API/account credentials, or edit the source corpus. Task/gold
inputs are used only by the local information-access diagnostic.

Run the audit after predictions finish; the same command also produces a clearly
marked interim report while artifacts are still arriving:

```bash
python3 -B -S information_access.py \
  --run /path/to/empirical/runs/original-core-main \
  --bundle /path/to/original_core_repair \
  --root /path/to/spectra \
  --relational /path/to/empirical/relational \
  --source-schema /path/to/contract_repair_v1/source_schema_frozen_v1.json \
  --output information_access_report.json \
  --probe-source --SQL-diagnostic
```

The main report retains all 350 frozen admitted task IDs and every planned
request stage. Its companion `information_access_report.summary.json` provides
counts and the full report's hash. During an active run, missing or partially
written artifacts remain pending. After generation closes, an unissued stage
(such as D_answer after a failed followup) stays in the planned-stage denominator
and receives no request-audit PASS. Requests are reconstructed from the public question and requested
format, frozen value-free schema, and saved source windows; they must match the
actual retained serialized messages and payload hash. No keyword comparison
with gold is used to declare prompt leakage.

Use the same command with the transport supplement's `--run` directory to audit
its effective requests. Cached outcomes point to the actual original requests;
replayed requests must additionally match original payload bytes and hashes.
Keep the original and supplemental run directories side by side when replaying
published artifacts. This avoids dependency on the authors' absolute paths.
Omit `--probe-source` and `--SQL-diagnostic` if the large source corpus/databases
are unavailable; exact request and public schema audits still run from the
retained requests, context, schema cards and SQL manifests.

After the 350-task supplement finishes, audit its transport integrity separately:

```bash
python3 -B -S recovery_validation.py \
  --original /path/to/empirical/runs/original-core-main \
  --supplement /path/to/empirical/runs/original-core-transport-supplement \
  --output transport_recovery_validation.json
python3 -B -S -m unittest discover -s . -p 'test_*.py' -q
```

That tool checks eligibility before provider generation, exact retained request
payloads, preserved initial context for newly possible D answers, unchanged
cached outcomes, retry exclusions and all 1,400 method records. It reads no gold
or performance scores. Account finances are outside its scope; reported usage
is the known experimental API cost, with unknown cost explicitly retained.
For the separately preregistered 21-task extension, pass its original/supplement
directories and `--expected-n 21`. It remains a separate cohort audit and does
not replace the 350-task report or retrospectively change either denominator.

Final local information-access reports are `information_access_original350.json`,
`information_access_recovered350.json`, `information_access_extension21.json` and
`information_access_recovered21.json`, with corresponding `.summary.json` files.
The published evidence package places its pinned runtime under `runtime/`; the
information-access tool selects that directory automatically. Extract the original
and supplementary `retained_runs/` archives side by side, and select the relevant
frozen 350 or 21 bundle extracted from `inputs/`. Supply `relational_manifests/`
as `--relational` and the repository's frozen graph schema as `--source-schema`.
Omit source probing and SQL diagnostics when the large local databases are unavailable.

`recovery_validation.py` checks the private original artifact hashes. Public copies
mask only provider account/key financial error details; their hashes therefore differ
at the recorded locations. For public byte verification, use the evidence package's
`runtime/verify_evidence.py`, which checks published archive hashes and explicit
`public_redactions.json` provenance. It does not claim to independently verify private
original bytes. Saved requests, model answers and experimental usage remain unchanged.

The source presence probe selects at most three unmistakable documentary IDs
per task from the existing gold record order. It checks bounded FTS candidates
for an exact literal in retained source text. These are deterministic offline
diagnostic anchors: no answer count, company name or content string is used as
an anchor, and no anchor enters any model request. Positive witnesses establish
literal presence only. A negative or interrupted bounded lookup establishes
neither corpus absence nor missing semantic support. The chosen sample is not
the full answer population. Source text and frozen graph cutoff/content equality
remain unverified.

The report separates corpus candidates, literal presence, windows actually sent,
and unestablished relation/answer support. Finite context cannot certify an entire
population or its count/distribution. The model's `complete` flag is a self-report.
Same-source SQL/graph encodings do not establish a causal storage advantage.

The engineering tool uses only source query plans and two invented fixtures:

```bash
python3 -B -S retrieval_engineering.py \
  --corpus /path/to/corpus/ran1.sqlite3 \
  --expression '"meeting" OR "tdocs"' \
  --output retrieval_engineering.json
python3 -B -S -m unittest test_information_access -q
```

It documents why BM25 plus stable metadata tie ordering requires a temporary
sort. A development-only variant exhausts the entire boundary-score group before
applying the same stable ordering. The fixture checks exact selection, including
dense ties; it does not measure optimized real-corpus performance, generate
benchmark predictions, or modify the frozen baseline.

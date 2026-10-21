# Reproducing decision-to-Spec traces with SPECTRA

SPECTRA connects Resolution, referenced CR and declared target Spec roles to reproduce a decision-to-Spec lookup. Each of the ten requested Spec identities has an active same-CR positive outcome in an original report and a matching formal-register target. The executable contract preserves the original path-count selection, complete two-column native output and requested Spec identity set.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 1 | 0.2985 | 0/1 | 0 |
| text2sql | 1 | 0.2985 | 0/1 | 0 |
| single_retrieval | 1 | 0.3333 | 0/1 | 0 |
| iterative_retrieval | 1 | 0.0000 | 0/1 | 1 |


Five logical requests produced five complete first responses at actual usage cost 0.294215 USD. Both structured methods recover all ten requested identities among57 returned identities (F1 0.29850746268656714). Single retrieval returns two requested identities (F1 0.33333333333333337); iterative retrieval abstains. Saved prompts, raw responses, generated queries, execution statuses and complete-record scores reproduce each outcome.

The evidence replays3,778 recorded paths and57 Spec groups, with active same-CR source witnesses for the selected ten identities across four reports and four registers. Two distinct seven-unit AI reviews, guarded native execution, independent SQL and16 requested-identity controls support the tracing and scoring procedure. Path counts supply the authored selection helper. Model inference uses anthropic/claude-opus-4.8 through Anthropic, byte-preserved scientific adapters, original prompt and token caps, and fixed transport policy. Review provenance records two nonblind AI reviews and human/expert count0.

Replay the saved evaluation locally:

    python3 -B -I runtime/verify_authorized_incremental43_evaluation.py --evidence . --bundle ../original_core_overnight_repairs43

The registration records the513-to-514 extension. The current all-560 index and disposition register provide release-wide accounting.

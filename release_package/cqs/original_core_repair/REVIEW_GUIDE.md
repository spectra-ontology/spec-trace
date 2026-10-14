# Reviewing the original-question repair set

Start with the unchanged original question in each itemized page. Compare the
two queries and the asked answer fields, then inspect the complete captured
native output. `tasks.jsonl` embeds both AI judgments with separate evidence for
requested roles, population, filters, counting unit, completeness, ordering and
additional inputs. It also pins the exact repaired definition and source bytes.
The offline verifier reprojects gold from native output, rechecks those hashes
and judgments, and checks all 560 disposition IDs against the unchanged release.
It cannot certify the truth of the AI semantic conclusions.

- [RAN1](changes/RAN1.md)
- [RAN2](changes/RAN2.md)
- [RAN3](changes/RAN3.md)
- [RAN4](changes/RAN4.md)
- [RAN5](changes/RAN5.md)

The disposition ledger covers every original Core ID. Only admitted repairs are
in the runnable task/gold set. The remaining originals are pending or blocked;
an itemized proposal or successful query execution alone is not admission.
The original release and historical results remain distinct from this supplement.

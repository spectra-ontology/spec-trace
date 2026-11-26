# Archived main-task exposure

The 20 archived main-workload packets give all four interfaces the same 667
questions and ordered output fields. `audit.json` connects each historical item
ID to its admitted item, records exact file and task hashes, preserves the task
text and inventories 106 archived query-writer prompts.

The query writers saw a schema and the question. The raw-document writers saw
the question and the record-search interface, with instructions to return an
empty answer when the records contain no such row. These input files establish
the historical access conditions. The released snapshot defines the recorded
gold used for scoring; a family-level explanation of that target is a separate
part of the benchmark documentation. The full-chain question requests “each
clause” modified by the CR. The archived tasks and prompts leave exact-clause,
subclause and projection-completeness semantics implicit.

Run the inventory check from the release root:

```sh
python3 -B benchmark/task_exposure/replay.py --release . \
  --out work/task_exposure.json
```

The check compares actual archived packet/task bytes and all question/field
bindings with the audit, then verifies the 106 original prompt-file hashes.
It uses the Python standard library and makes no model calls. This inventory
preserves the historical experiments and makes their actual instructions
inspectable.

## Solver instructions for new runs

Use [solver instructions v1](solver_wrapper_v1.txt) as the identical initial
text of every solver prompt for the main or order-and-neighbour workload.
Follow it with the condition's schema, tools and output format. Deliver each
answer-free question packet through its existing interface. For a matched
comparison, keep the wrapper bytes, questions and field order fixed.
Put the wrapper version and SHA-256 beside the exact sent packet in the run
manifest. Schema-only packets retain their original value access policy.
The v1 prefix contains no item outcome or native scope literal.

The historical audit above describes archived prompts. New-run results under
v1 have their own exposure record.

The [full-chain source-label sensitivity](full_chain/README.md) compares all
100 affected-clause fields with released gold and replays the saved answers.

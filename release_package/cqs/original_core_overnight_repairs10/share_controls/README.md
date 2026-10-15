This sidecar preserves the exact Samsung share question and measured controls.

Run `python3 -B -S replay_saved_controls.py --out NEW_RECEIPT.json`.

It replays the original 20 controls and the later 24-control native/SQL gate separately. These sets overlap; 44 is not a count of independent cases. It also reruns 25 source-free public prompt, parser, exact decimal, assembly and scoring checks. No research SQLite database, graph, model API or network is used. The 25-check suite creates one temporary synthetic SQLite database and a private empty `.git` directory solely to satisfy the unchanged runtime's repository-root discovery. This does not invoke Git or access a repository. Native execution is simulated only in the explicitly named synthetic check.

The saved native and two-SQL gate is provenance, not a new native run. Semantic reviews are AI development checks; human expert reviews: zero. The public scorer's original typed matcher bytes remain unchanged; the declared exact-rational wrapper normalizes equivalent candidate forms before that matcher. Ordinary tasks retain their original behavior.

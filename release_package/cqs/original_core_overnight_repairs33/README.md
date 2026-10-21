# Tracing PUSCH repetition decisions

The ontology connects recorded Agreements and Meetings with retained clause,
table and change-request context to preserve substantive PUSCH repetition
decisions and their conditions. The original question, literal selector,
numeric meeting order and ten-record extent are preserved. Exact native output,
independent SQL and two AI semantic reviews make the trace reproducible.

    python3 -B -I -S verify_additions.py --bundle .

The replay checks all532 matched records and the complete16-record boundary,
plus original XML and typed negative controls. Any legitimate ten records at
the cutoff are accepted. No live model or native query is called by verification.

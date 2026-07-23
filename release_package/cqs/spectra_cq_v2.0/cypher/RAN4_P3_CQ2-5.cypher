// SpectraCQ RAN4_P3_CQ2-5 (RAN4, phase 3) -- CQ2_TS
// Question: List the top 10 cross-spec section-reference pairs (inter-spec dependency map).
// Gold: 4 rows, primary column "fromSpec"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10

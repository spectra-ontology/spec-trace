// SpectraCQ RAN5_P3_CQ2-4 (RAN5, phase 3) -- CQ2_TS
// Question: Which spec-to-spec section-reference pairs are most frequent? (cross-spec coupling)
// Gold: 4 rows, primary column "fromSpec"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10

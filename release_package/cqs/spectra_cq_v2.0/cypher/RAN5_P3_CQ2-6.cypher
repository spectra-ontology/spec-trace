// SpectraCQ RAN5_P3_CQ2-6 (RAN5, phase 3) -- CQ2_TS
// Question: Which ten spec-to-spec reference pairs are most frequent? (cross-spec dependencies)
// Gold: 10 rows, primary column "fromSpec"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sa:Spec), (a)-[:REFERENCES_SPEC]->(sb:Spec) WHERE sa.specNumber <> sb.specNumber RETURN sa.specNumber AS fromSpec, sb.specNumber AS toSpec, count(*) AS refCount ORDER BY refCount DESC LIMIT 10

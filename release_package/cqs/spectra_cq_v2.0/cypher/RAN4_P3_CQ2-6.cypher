// SpectraCQ RAN4_P3_CQ2-6 (RAN4, phase 3) -- CQ2_TS
// Question: List the top 5 specs referenced by spec 38.101-1 (its main dependencies).
// Gold: 4 rows, primary column "target.specNumber"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.101-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC LIMIT 5

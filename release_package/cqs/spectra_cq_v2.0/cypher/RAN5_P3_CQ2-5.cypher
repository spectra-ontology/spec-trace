// SpectraCQ RAN5_P3_CQ2-5 (RAN5, phase 3) -- CQ2_TS
// Question: Which five specs does TS 38.521-1 reference most? (dependency ranking)
// Gold: 5 rows, primary column "target.specNumber"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.521-1'}), (a)-[:REFERENCES_SPEC]->(target:Spec) RETURN target.specNumber, count(*) AS refCount ORDER BY refCount DESC, target.specNumber LIMIT 5

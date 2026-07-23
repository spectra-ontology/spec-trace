// SpectraCQ RAN4_P3_CQ5-3 (RAN4, phase 3) -- CQ5
// Question: List the top 10 specs changed in Rel-18 (release change scope).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.1' RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10

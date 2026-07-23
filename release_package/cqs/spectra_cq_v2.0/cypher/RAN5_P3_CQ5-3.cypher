// SpectraCQ RAN5_P3_CQ5-3 (RAN5, phase 3) -- CQ5
// Question: Which RAN5 specs were changed in each release? (release-level change map)
// Gold: 10 rows, primary column "rel.releaseName"

MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN rel.releaseName, sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10

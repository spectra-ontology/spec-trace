// SpectraCQ RAN2_P3_CQ3-8 (RAN2, phase 3) -- CQ3_CR
// Question: Return the top 5 specs by Rel-18 CR count (release change footprint).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCnt ORDER BY crCnt DESC LIMIT 5

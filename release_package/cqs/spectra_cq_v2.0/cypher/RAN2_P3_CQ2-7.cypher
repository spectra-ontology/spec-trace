// SpectraCQ RAN2_P3_CQ2-7 (RAN2, phase 3) -- CQ2_TS
// Question: Return the top 5 specs by intra-spec reference count (internal cohesion).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber, count(*) AS intraRefs ORDER BY intraRefs DESC LIMIT 5

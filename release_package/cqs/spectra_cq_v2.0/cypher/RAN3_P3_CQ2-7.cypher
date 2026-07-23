// SpectraCQ RAN3_P3_CQ2-7 (RAN3, phase 3) -- CQ2_TS
// Question: Return the top 5 specs by intra-spec references (internal-cohesion metric).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (s1)-[:REFERENCES_SECTION]->(s2:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN sp.specNumber, count(*) AS intraRefs ORDER BY intraRefs DESC LIMIT 5

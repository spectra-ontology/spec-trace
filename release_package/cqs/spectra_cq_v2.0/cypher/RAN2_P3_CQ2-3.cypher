// SpectraCQ RAN2_P3_CQ2-3 (RAN2, phase 3) -- CQ2_TS
// Question: Which sections of spec 38.321 make the most references (reference hub)?
// Gold: 10 rows, primary column "s2.sectionId"

MATCH (s1:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.321'}), (s1)-[:REFERENCES_SECTION]->(s2:Section) RETURN s2.sectionId, count(*) AS refs ORDER BY refs DESC LIMIT 10

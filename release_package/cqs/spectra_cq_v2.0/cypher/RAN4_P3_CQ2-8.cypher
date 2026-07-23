// SpectraCQ RAN4_P3_CQ2-8 (RAN4, phase 3) -- CQ2_TS
// Question: How many internal cross-references does spec 38.133 have? (self-reference density).
// Gold: 1 rows, primary column "internalRefs"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.133'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs

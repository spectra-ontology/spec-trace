// SpectraCQ RAN5_P3_CQ2-7 (RAN5, phase 3) -- CQ2_TS
// Question: How many internal cross-references does TS 38.533 contain? (self-reference density)
// Gold: 1 rows, primary column "internalRefs"

MATCH (a:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (a)-[:REFERENCES_SECTION]->(b:Section)-[:BELONGS_TO_SPEC]->(sp) RETURN count(*) AS internalRefs

// SpectraCQ RAN5_P3_CQ1-14 (RAN5, phase 3) -- CQ1_TS
// Question: How many tables does TS 38.533 contain? (table count)
// Gold: 1 rows, primary column "tableCount"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber: '38.533'}), (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN count(t) AS tableCount

// SpectraCQ RAN1_P3_CQ033 (RAN1, phase 3) -- 
// Question: Show the PUSCH-related sections and tables (scope for uplink data-channel implementation).
// Gold: 28 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PUSCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber

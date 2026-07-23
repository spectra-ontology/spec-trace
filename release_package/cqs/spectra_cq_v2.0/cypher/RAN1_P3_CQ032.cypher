// SpectraCQ RAN1_P3_CQ032 (RAN1, phase 3) -- 
// Question: Show the PDCCH-related sections and tables (full scope for control-channel implementation).
// Gold: 15 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) WHERE sec.sectionTitle =~ '(?i).*PDCCH.*' OPTIONAL MATCH (sec)-[:CONTAINS_TABLE]->(tbl:TSTable) RETURN sp.specNumber, sec.sectionNumber, sec.sectionTitle, sec.level, collect(tbl.tableNumber) AS tables ORDER BY sp.specNumber, sec.sectionNumber

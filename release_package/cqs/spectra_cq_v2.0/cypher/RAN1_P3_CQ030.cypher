// SpectraCQ RAN1_P3_CQ030 (RAN1, phase 3) -- 
// Question: List the CSI-related tables (parameter tables for CSI-reporting implementation).
// Gold: 20 rows, primary column "sp.specNumber"

MATCH (tbl:TSTable) WHERE tbl.tableCaption =~ '(?i).*CSI.*' MATCH (tbl)-[:TABLE_IN_SECTION]->(sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, tbl.tableNumber, tbl.tableCaption, sec.sectionNumber ORDER BY sp.specNumber, tbl.tableNumber LIMIT 20

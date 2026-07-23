// SpectraCQ RAN5_P3_CQ1-10 (RAN5, phase 3) -- CQ1_TS
// Question: Locate the spec and section for tables numbered 6.2.x (table-number lookup).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable) WHERE t.tableNumber STARTS WITH '6.2' RETURN sp.specNumber, sec.sectionId, t.tableNumber, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10

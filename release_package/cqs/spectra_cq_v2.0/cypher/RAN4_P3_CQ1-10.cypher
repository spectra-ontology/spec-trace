// SpectraCQ RAN4_P3_CQ1-10 (RAN4, phase 3) -- CQ1_TS
// Question: Find the spec and section that hold table 4.3-1 (reverse table lookup).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec), (sec)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber: '4.3-1'}) RETURN sp.specNumber, sec.sectionId, t.tableCaption ORDER BY sp.specNumber, sec.sectionId, t.tableId LIMIT 10

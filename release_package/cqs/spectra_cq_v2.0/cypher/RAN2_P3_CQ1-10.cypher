// SpectraCQ RAN2_P3_CQ1-10 (RAN2, phase 3) -- CQ1_TS
// Question: Find the spec and section that hold Table 6.3.3-1 (reverse table lookup).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (t:TSTable {tableNumber: '6.3.3-1'})-[:TABLE_IN_SECTION]->(s:Section)-[:BELONGS_TO_SPEC]->(sp:Spec) RETURN sp.specNumber, s.sectionId, t.tableId

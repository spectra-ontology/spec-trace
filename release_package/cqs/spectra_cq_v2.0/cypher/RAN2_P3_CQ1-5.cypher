// SpectraCQ RAN2_P3_CQ1-5 (RAN2, phase 3) -- CQ1_TS
// Question: List the tables in section 6.2.1 of spec 38.321 (table lookup).
// Gold: 8 rows, primary column "t.tableId"

MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'6.2.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption

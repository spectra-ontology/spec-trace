// SpectraCQ RAN5_P3_CQ1-5 (RAN5, phase 3) -- CQ1_TS
// Question: List the tables in section 6.2.3 of TS 38.521-1 (table lookup).
// Gold: 1 rows, primary column "t.tableId"

MATCH (rk:Spec {specNumber:'38.521-1'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'6.2.3'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25

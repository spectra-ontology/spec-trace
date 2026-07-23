// SpectraCQ RAN4_P3_CQ1-5 (RAN4, phase 3) -- CQ1_TS
// Question: List the tables in section 9.2.5.1 of spec 38.133 (locating requirement tables).
// Gold: 25 rows, primary column "t.tableId"

MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'9.2.5.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption ORDER BY t.tableNumber LIMIT 25

// SpectraCQ RAN3_P3_CQ1-5 (RAN3, phase 3) -- CQ1_TS
// Question: List the tables in section 8.1 of spec 38.413 (finding tabular content).
// Gold: 2 rows, primary column "t.tableId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'8.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:CONTAINS_TABLE]->(t:TSTable) RETURN t.tableId, t.tableNumber, t.tableCaption

// SpectraCQ RAN4_P3_CQ1-7 (RAN4, phase 3) -- CQ1_TS
// Question: Which section of spec 38.101-1 contains table 5.2-1? (locating a table's context).
// Gold: 1 rows, primary column "sec.sectionId"

MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(sec:Section)-[:CONTAINS_TABLE]->(t:TSTable {tableNumber:'5.2-1'}) WHERE rk.specRelease IS NOT NULL WITH sec,t,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN sec.sectionId, sec.sectionNumber, sec.sectionTitle

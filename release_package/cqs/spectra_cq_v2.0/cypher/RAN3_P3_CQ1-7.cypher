// SpectraCQ RAN3_P3_CQ1-7 (RAN3, phase 3) -- CQ1_TS
// Question: Return the section that contains Table 8.1-1 of spec 38.413 (table-to-section lookup).
// Gold: 1 rows, primary column "sec.sectionId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(t:TSTable {tableNumber:'8.1-1'}) WHERE rk.specRelease IS NOT NULL WITH sec,t,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN sec.sectionId, sec.sectionTitle

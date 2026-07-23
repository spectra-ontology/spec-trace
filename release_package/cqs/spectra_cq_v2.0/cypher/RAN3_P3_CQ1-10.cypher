// SpectraCQ RAN3_P3_CQ1-10 (RAN3, phase 3) -- CQ1_TS
// Question: Find the spec and section for Table 8.1-1 of spec 38.423 (table-provenance lookup).
// Gold: 1 rows, primary column "rk.specNumber"

MATCH (rk:Spec {specNumber:'38.423'})<-[:BELONGS_TO_SPEC]-(sec:Section)<-[:TABLE_IN_SECTION]-(t:TSTable {tableNumber:'8.1-1'}) WHERE rk.specRelease IS NOT NULL WITH rk,sec,t ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 RETURN rk.specNumber, sec.sectionId, t.tableCaption

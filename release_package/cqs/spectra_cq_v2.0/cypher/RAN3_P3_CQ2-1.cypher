// SpectraCQ RAN3_P3_CQ2-1 (RAN3, phase 3) -- CQ2_TS
// Question: List the sections that section 10.1 of spec 38.413 references (outgoing cross-references).
// Gold: 1 rows, primary column "target.sectionId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10.1'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (sec)-[:REFERENCES_SECTION]->(target:Section) RETURN target.sectionId, target.sectionTitle

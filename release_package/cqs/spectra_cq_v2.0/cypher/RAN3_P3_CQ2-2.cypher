// SpectraCQ RAN3_P3_CQ2-2 (RAN3, phase 3) -- CQ2_TS
// Question: List the sections that reference section 10 of spec 38.413 (incoming cross-references).
// Gold: 4 rows, primary column "src.sectionId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber:'10'}) WHERE rk.specRelease IS NOT NULL WITH sec,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (src:Section)-[:REFERENCES_SECTION]->(sec) RETURN src.sectionId, src.sectionTitle

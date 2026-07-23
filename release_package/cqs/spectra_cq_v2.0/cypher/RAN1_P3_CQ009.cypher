// SpectraCQ RAN1_P3_CQ009 (RAN1, phase 3) -- TS
// Question: Which sections does TS 38.214 Section 5.1 reference? (companion reading for implementation)
// Gold: 5 rows, primary column "tgt.sectionNumber"

MATCH (rk:Spec {specNumber:'38.214'})<-[:BELONGS_TO_SPEC]-(src:Section {sectionNumber:'5.1'}) WHERE rk.specRelease IS NOT NULL WITH src, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (src)-[:REFERENCES_SECTION]->(tgt:Section) RETURN tgt.sectionNumber, tgt.sectionTitle ORDER BY tgt.sectionNumber

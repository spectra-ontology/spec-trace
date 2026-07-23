// SpectraCQ RAN2_P3_CQ2-2 (RAN2, phase 3) -- CQ2_TS
// Question: List the sections that reference section 5.4.3.1 of spec 38.321 (incoming references).
// Gold: 15 rows, primary column "ref.sectionId"

MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'5.4.3.1'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (ref:Section)-[:REFERENCES_SECTION]->(s) RETURN ref.sectionId, ref.sectionTitle ORDER BY ref.sectionId

// SpectraCQ RAN2_P3_CQ2-1 (RAN2, phase 3) -- CQ2_TS
// Question: List the sections referenced by section 5.4.4 of spec 38.321 (outgoing references).
// Gold: 19 rows, primary column "ref.sectionId"

MATCH (rk:Spec {specNumber:'38.321'})<-[:BELONGS_TO_SPEC]-(s:Section {sectionNumber:'5.4.4'}) WHERE rk.specRelease IS NOT NULL WITH s, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (s)-[:REFERENCES_SECTION]->(ref:Section) RETURN ref.sectionId, ref.sectionTitle ORDER BY ref.sectionId

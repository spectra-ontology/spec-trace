// SpectraCQ RAN4_P3_CQ2-1 (RAN4, phase 3) -- CQ2_TS
// Question: List the sections referenced by section 3.2 of spec 38.101-1 (outbound cross-references).
// Gold: 4 rows, primary column "b.sectionId"

MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(a:Section {sectionNumber:'3.2'}) WHERE rk.specRelease IS NOT NULL WITH a,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a)-[:REFERENCES_SECTION]->(b:Section) RETURN b.sectionId, b.sectionTitle ORDER BY b.sectionNumber LIMIT 25

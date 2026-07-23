// SpectraCQ RAN3_P3_CQ1-2 (RAN3, phase 3) -- CQ1_TS
// Question: List the subsections of section 9.3.1 in spec 38.413 (navigating IE definitions).
// Gold: 15 rows, primary column "c.sectionId"

MATCH (rk:Spec {specNumber:'38.413'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'9.3.1'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 15

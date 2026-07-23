// SpectraCQ RAN4_P3_CQ1-12 (RAN4, phase 3) -- CQ1_TS
// Question: List the sub-sections of section 6 in spec 38.101-1 (drilling into a clause).
// Gold: 25 rows, primary column "c.sectionId"

MATCH (rk:Spec {specNumber:'38.101-1'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'6'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25

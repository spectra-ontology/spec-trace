// SpectraCQ RAN4_P3_CQ1-2 (RAN4, phase 3) -- CQ1_TS
// Question: List the sub-sections of section 10.1 in spec 38.133 (drilling into a clause).
// Gold: 25 rows, primary column "c.sectionId"

MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'10.1'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25

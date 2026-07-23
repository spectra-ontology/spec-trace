// SpectraCQ RAN5_P3_CQ1-12 (RAN5, phase 3) -- CQ1_TS
// Question: List the subsections under section 7 of TS 38.523-1 (drilling into a clause).
// Gold: 1 rows, primary column "c.sectionId"

MATCH (rk:Spec {specNumber:'38.523-1'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'7'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25

// SpectraCQ RAN5_P3_CQ1-2 (RAN5, phase 3) -- CQ1_TS
// Question: List the subsections under section 5 of TS 38.533 (drilling into a clause).
// Gold: 8 rows, primary column "c.sectionId"

MATCH (rk:Spec {specNumber:'38.533'})<-[:BELONGS_TO_SPEC]-(p:Section {sectionNumber:'5'}) WHERE rk.specRelease IS NOT NULL WITH p,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN c.sectionId, c.sectionNumber, c.sectionTitle ORDER BY c.sectionNumber LIMIT 25

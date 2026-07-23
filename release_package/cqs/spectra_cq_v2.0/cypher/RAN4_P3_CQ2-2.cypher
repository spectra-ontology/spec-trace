// SpectraCQ RAN4_P3_CQ2-2 (RAN4, phase 3) -- CQ2_TS
// Question: List the sections that reference section 4.2 of spec 38.133 (inbound cross-references).
// Gold: 25 rows, primary column "a.sectionId"

MATCH (rk:Spec {specNumber:'38.133'})<-[:BELONGS_TO_SPEC]-(b:Section {sectionNumber:'4.2'}) WHERE rk.specRelease IS NOT NULL WITH b,rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (a:Section)-[:REFERENCES_SECTION]->(b) RETURN a.sectionId ORDER BY a.sectionId LIMIT 25

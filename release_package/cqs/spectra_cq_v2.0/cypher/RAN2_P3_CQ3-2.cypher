// SpectraCQ RAN2_P3_CQ3-2 (RAN2, phase 3) -- CQ3_CR
// Question: Return the top-level sections of spec 38.331 that CRs modify (CR-target layout).
// Gold: 10 rows, primary column "s.sectionNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.331'}) WHERE hub.specRelease IS NULL WITH hub LIMIT 1 MATCH (rk:Spec {specNumber:'38.331'})-[:IN_RELEASE_OF]->(hub) WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (rk)<-[:BELONGS_TO_SPEC]-(s:Section {level: 1}) RETURN s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 10

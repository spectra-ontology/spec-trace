// SpectraCQ RAN3_P3_CQ3-2 (RAN3, phase 3) -- CQ3_CR
// Question: Show the level-1 section structure of spec 38.423 targeted by CRs (change-context overview).
// Gold: 10 rows, primary column "s.sectionNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.423'}) WHERE hub.specRelease IS NULL WITH DISTINCT hub MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC LIMIT 1 MATCH (rk)<-[:BELONGS_TO_SPEC]-(s:Section {level:1}) RETURN s.sectionNumber, s.sectionTitle ORDER BY s.sectionNumber LIMIT 10

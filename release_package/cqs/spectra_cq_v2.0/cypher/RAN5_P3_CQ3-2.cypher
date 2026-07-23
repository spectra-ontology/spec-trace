// SpectraCQ RAN5_P3_CQ3-2 (RAN5, phase 3) -- CQ3_CR
// Question: For TS 38.521-1, report its CR count alongside its section total (change-and-structure summary).
// Gold: 1 rows, primary column "specNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.521-1'}) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber AS specNumber, crCount, count(s) AS sectionCount

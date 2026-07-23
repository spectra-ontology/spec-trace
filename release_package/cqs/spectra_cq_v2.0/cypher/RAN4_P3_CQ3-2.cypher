// SpectraCQ RAN4_P3_CQ3-2 (RAN4, phase 3) -- CQ3_CR
// Question: How many CRs modify spec 38.133, and how many sections does it have? (change load vs spec size).
// Gold: 1 rows, primary column "hub.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec {specNumber:'38.133'}) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber, crCount, count(s) AS sectionCount

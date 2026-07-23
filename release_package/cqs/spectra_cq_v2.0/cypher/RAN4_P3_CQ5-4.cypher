// SpectraCQ RAN4_P3_CQ5-4 (RAN4, phase 3) -- CQ5
// Question: List the top 10 RAN4 specs with the most CRs (most-revised specs).
// Gold: 10 rows, primary column "hub.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(hub:Spec) WHERE hub.specRelease IS NULL AND hub.specNumber STARTS WITH '38.1' WITH hub, count(cr) AS crCount MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCount, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCount, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) RETURN hub.specNumber, crCount, count(s) AS sectionCount ORDER BY crCount DESC LIMIT 10

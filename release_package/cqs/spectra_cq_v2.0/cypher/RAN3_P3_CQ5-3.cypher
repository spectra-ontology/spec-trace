// SpectraCQ RAN3_P3_CQ5-3 (RAN3, phase 3) -- CQ5
// Question: Return CR density (CRs per section) for each spec (change-intensity metric).
// Gold: 5 rows, primary column "specNumber"

MATCH (hub:Spec)<-[:MODIFIES]-(cr:CR) WHERE hub.specRelease IS NULL WITH hub, count(cr) AS crCnt MATCH (rk:Spec)-[:IN_RELEASE_OF]->(hub) WITH hub, crCnt, rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC WITH hub, crCnt, collect(rk)[0] AS latestRk MATCH (latestRk)<-[:BELONGS_TO_SPEC]-(s:Section) WITH hub, crCnt, count(s) AS secCnt RETURN hub.specNumber AS specNumber, crCnt, secCnt, round(1.0 * crCnt / secCnt, 2) AS density ORDER BY density DESC LIMIT 5

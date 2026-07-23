// SpectraCQ RAN1_P3_CQ045 (RAN1, phase 3) -- Resolution_TS
// Question: Which TSs did resolutions on NR_FeMIMO-Core CRs land in? (how this work item's decisions entered the standard)
// Gold: 3 rows, primary column "spec"

MATCH (w:WorkItem {workItemCode: 'NR_FeMIMO-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) MATCH (res:Resolution)-[:REFERENCES]->(cr) RETURN sp.specNumber AS spec, count(DISTINCT res) AS resolutionCount, count(DISTINCT cr) AS crCount ORDER BY resolutionCount DESC

// SpectraCQ RAN1_P3_CQ044 (RAN1, phase 3) -- CR_TS
// Question: List the TSs modified by CRs under Work Item NR_newRAT-Core (portfolio impact of this work item).
// Gold: 16 rows, primary column "spec"

MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(cr) AS crCount ORDER BY crCount DESC

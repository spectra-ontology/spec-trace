// SpectraCQ P3_CQ044 — CR_TS_변경추적
// Question (English): Return TSes affected by CRs from Work Item NR_newRAT-Core (work-item portfolio analysis).
// Schema area: classes=['CR', 'Spec', 'WorkItem'], rels=['MODIFIES', 'RELATED_TO']

MATCH (w:WorkItem {workItemCode: 'NR_newRAT-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber AS spec, count(cr) AS crCount ORDER BY crCount DESC

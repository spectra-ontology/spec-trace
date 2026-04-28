// SpectraCQ P3_CQ045 — Resolution_TS_의사결정
// Question (English): Return TSes whose Resolutions affected CRs from Work Item NR_FeMIMO-Core (work-item-to-standard tracing).
// Schema area: classes=['CR', 'Resolution', 'Spec', 'WorkItem'], rels=['MODIFIES', 'REFERENCES', 'RELATED_TO']

MATCH (w:WorkItem {workItemCode: 'NR_FeMIMO-Core'})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(sp:Spec) MATCH (res:Resolution)-[:REFERENCES]->(cr) RETURN sp.specNumber AS spec, count(DISTINCT res) AS resolutionCount, count(DISTINCT cr) AS crCount ORDER BY resolutionCount DESC

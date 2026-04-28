// SpectraCQ P1_CQ3-3 — CQ3_회사분석
// Question (English): Return the top-10 companies by contribution count to Work Item NR_unlic-Core (competitive landscape per technology area).
// Schema area: classes=['Company', 'Tdoc', 'WorkItem'], rels=['RELATED_TO', 'SUBMITTED_BY']

MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10

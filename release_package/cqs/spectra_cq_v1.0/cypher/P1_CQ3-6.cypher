// SpectraCQ P1_CQ3-6 — CQ3_회사분석
// Question (English): Return HiSilicon's top-10 work items by contribution count (technology-leadership distribution).
// Schema area: classes=['Company', 'Tdoc', 'WorkItem'], rels=['RELATED_TO', 'SUBMITTED_BY']

MATCH (c:Company {companyName: 'HiSilicon'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS tdocCount ORDER BY tdocCount DESC, wi.workItemCode ASC LIMIT 10

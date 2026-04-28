// SpectraCQ P1_CQ4-1 — CQ4_회의히스토리
// Question (English): List CompanyE's prior TDocs in Work Item NR_eMIMO-Core across past meetings (technology-history tracing).
// Schema area: classes=['Company', 'Meeting', 'Tdoc', 'WorkItem'], rels=['PRESENTED_AT', 'RELATED_TO', 'SUBMITTED_BY']

MATCH (c:Company {companyName: 'CompanyE'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.meetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

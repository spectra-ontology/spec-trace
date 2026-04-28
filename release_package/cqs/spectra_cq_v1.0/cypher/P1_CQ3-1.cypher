// SpectraCQ P1_CQ3-1 — CQ3_회사분석
// Question (English): List the TDocs submitted by CompanyE under Work Item NR_MIMO_evo_DL_UL-Core.
// Schema area: classes=['Company', 'Tdoc', 'WorkItem'], rels=['RELATED_TO', 'SUBMITTED_BY']

MATCH (c:Company {companyName: 'CompanyE'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_MIMO_evo_DL_UL-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10

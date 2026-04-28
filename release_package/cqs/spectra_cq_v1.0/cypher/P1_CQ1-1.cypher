// SpectraCQ P1_CQ1-1 — CQ1_Tdoc기본검색
// Question (English): List the TDocs presented at meeting RAN1#120 that are linked to Work Item NR_eMIMO-Core (MIMO meeting preparation).
// Schema area: classes=['Meeting', 'Tdoc', 'WorkItem'], rels=['PRESENTED_AT', 'RELATED_TO']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

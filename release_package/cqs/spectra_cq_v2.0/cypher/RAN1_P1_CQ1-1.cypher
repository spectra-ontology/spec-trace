// SpectraCQ RAN1_P1_CQ1-1 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs at meeting RAN1#120 tied to Work Item NR_eMIMO-Core (MIMO meeting preparation).
// Gold: 2 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

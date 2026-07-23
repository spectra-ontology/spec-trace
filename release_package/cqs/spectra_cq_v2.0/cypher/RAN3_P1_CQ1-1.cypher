// SpectraCQ RAN3_P1_CQ1-1 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List the TDocs at meeting RAN3#130 linked to Work Item NR_newRAT-Core (interface work-item preparation).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber LIMIT 10

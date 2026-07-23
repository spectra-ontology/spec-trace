// SpectraCQ RAN1_P1_CQ4-1 (RAN1, phase 1) -- CQ4
// Question: List Samsung's contributions to Work Item NR_eMIMO-Core across past meetings (tracing a technical history).
// Gold: 10 rows, primary column "m.meetingNumber"

MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.meetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

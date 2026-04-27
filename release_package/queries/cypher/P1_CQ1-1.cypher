// P1_CQ1-1 — Phase 1 (Tdoc metadata)
// List the Tdocs presented at meeting RAN1#120 that are linked to Work Item NR_eMIMO-Core.

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_eMIMO-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

// SpectraCQ RAN2_P1_CQ4-1 (RAN2, phase 1) -- CQ4
// Question: List Samsung's contributions to Work Item NR_Mob_enh2-Core across earlier meetings (contribution history).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

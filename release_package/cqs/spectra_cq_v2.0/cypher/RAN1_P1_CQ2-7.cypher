// SpectraCQ RAN1_P1_CQ2-7 (RAN1, phase 1) -- CQ2_Tdoc
// Question: List the incoming LSs (LS in) at meeting RAN1#120 and their agenda items (reviewing other WGs' requests).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg ORDER BY t.tdocNumber ASC LIMIT 10

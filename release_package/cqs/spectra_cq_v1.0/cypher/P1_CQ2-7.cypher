// SpectraCQ P1_CQ2-7 — CQ2_Tdoc관계추적
// Question (English): List incoming LSes received at RAN1#120 with their associated agenda items (cross-WG-request review).
// Schema area: classes=['AgendaItem', 'Meeting', 'Tdoc', 'WorkingGroup'], rels=['BELONGS_TO', 'ORIGINATED_FROM', 'PRESENTED_AT']

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {type: 'LS in'})-[:BELONGS_TO]->(a:AgendaItem) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(wg:WorkingGroup) RETURN t.tdocNumber, t.title, a.agendaNumber, wg.wgName AS from_wg ORDER BY t.tdocNumber ASC LIMIT 10

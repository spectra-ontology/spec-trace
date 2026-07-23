// SpectraCQ RAN2_P1_CQ3-2 (RAN2, phase 1) -- CQ3
// Question: List all companies' contributions under Agenda Item 8.2.2 (Ambient IoT) at RAN2#130 (A-IoT landscape).
// Gold: 10 rows, primary column "c.companyName"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.2.2'}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10

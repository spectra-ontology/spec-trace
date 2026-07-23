// SpectraCQ RAN1_P1_CQ2-6 (RAN1, phase 1) -- CQ2_Tdoc
// Question: List the TDocs postponed to the next meeting at RAN1#120 (tracking open items).
// Gold: 3 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc {status: 'postponed'}) RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10

// SpectraCQ RAN1_P1_CQ1-5 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the TDocs approved or agreed at meeting RAN1#121.
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {meetingNumber: 'RAN1#121'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

// SpectraCQ RAN2_P1_CQ1-5 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List the TDocs approved or agreed at meeting RAN2#131 (meeting outcome review).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status IN ['approved', 'agreed'] RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10

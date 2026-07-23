// SpectraCQ RAN2_P1_CQ2-6 (RAN2, phase 1) -- CQ2_Tdoc
// Question: List the TDocs postponed to a later meeting at RAN2#131 (deferred-item tracking).
// Gold: 9 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#131'})<-[:PRESENTED_AT]-(t:Tdoc) WHERE t.status = 'postponed' RETURN t.tdocNumber, t.title, t.type ORDER BY t.tdocNumber ASC LIMIT 10

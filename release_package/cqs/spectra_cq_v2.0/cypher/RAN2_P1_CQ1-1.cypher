// SpectraCQ RAN2_P1_CQ1-1 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List the TDocs at meeting RAN2#130 linked to Work Item NR_Mob_enh2-Core (mobility-enhancement meeting prep).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#130'})<-[:PRESENTED_AT]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_Mob_enh2-Core'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY t.tdocNumber ASC LIMIT 10

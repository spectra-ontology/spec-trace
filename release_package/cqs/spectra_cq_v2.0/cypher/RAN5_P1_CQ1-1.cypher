// SpectraCQ RAN5_P1_CQ1-1 (RAN5, phase 1) -- 
// Question: List the TDocs presented at meeting RAN5#109 (meeting document survey).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10

// SpectraCQ RAN4_P1_CQ1-1 (RAN4, phase 1) -- 
// Question: List the TDocs presented at meeting RAN4#113 (meeting document overview).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#113'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10

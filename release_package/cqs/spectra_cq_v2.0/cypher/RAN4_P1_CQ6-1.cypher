// SpectraCQ RAN4_P1_CQ6-1 (RAN4, phase 1) -- 
// Question: How many TDocs were presented at meeting RAN4#117? (meeting size).
// Gold: 1 rows, primary column "cnt"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN4#117'}) RETURN count(t) AS cnt

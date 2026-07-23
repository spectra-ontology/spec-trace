// SpectraCQ RAN5_P1_CQ6-1 (RAN5, phase 1) -- 
// Question: How many TDocs were presented at meeting RAN5#109? (meeting volume)
// Gold: 1 rows, primary column "cnt"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {canonicalMeetingNumber:'RAN5#109'}) RETURN count(t) AS cnt

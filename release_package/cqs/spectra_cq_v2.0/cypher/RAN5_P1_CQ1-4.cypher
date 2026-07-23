// SpectraCQ RAN5_P1_CQ1-4 (RAN5, phase 1) -- 
// Question: Which five meetings hosted the most TDocs? (activity ranking)
// Gold: 5 rows, primary column "m.canonicalMeetingNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5

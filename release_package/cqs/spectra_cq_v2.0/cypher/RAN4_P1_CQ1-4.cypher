// SpectraCQ RAN4_P1_CQ1-4 (RAN4, phase 1) -- 
// Question: List the top 5 meetings by number of TDocs (busiest meetings).
// Gold: 5 rows, primary column "m.canonicalMeetingNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(t) AS cnt ORDER BY cnt DESC LIMIT 5

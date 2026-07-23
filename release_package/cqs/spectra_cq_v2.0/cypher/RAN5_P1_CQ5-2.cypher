// SpectraCQ RAN5_P1_CQ5-2 (RAN5, phase 1) -- 
// Question: Show TDoc counts per meeting, most recent first (coverage check).
// Gold: 5 rows, primary column "m.canonicalMeetingNumber"

MATCH (m:Meeting) WITH m OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m, count(t) AS tdocs RETURN m.canonicalMeetingNumber, tdocs ORDER BY m.meetingNumberInt DESC LIMIT 5

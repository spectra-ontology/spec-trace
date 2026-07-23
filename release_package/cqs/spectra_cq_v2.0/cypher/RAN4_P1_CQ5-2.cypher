// SpectraCQ RAN4_P1_CQ5-2 (RAN4, phase 1) -- 
// Question: Show the most recent meetings and their TDoc counts (meeting coverage check).
// Gold: 5 rows, primary column "m.canonicalMeetingNumber"

MATCH (m:Meeting) WITH m OPTIONAL MATCH (t:Tdoc)-[:PRESENTED_AT]->(m) WITH m, count(t) AS tdocs RETURN m.canonicalMeetingNumber, tdocs ORDER BY m.meetingNumberInt DESC, m.canonicalMeetingNumber LIMIT 5

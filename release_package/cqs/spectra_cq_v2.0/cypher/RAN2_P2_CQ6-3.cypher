// SpectraCQ RAN2_P2_CQ6-3 (RAN2, phase 2) -- CQ6
// Question: Return the trend of agreement counts per meeting (activity trend).
// Gold: 58 rows, primary column "m.canonicalMeetingNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(a) AS agrCount ORDER BY m.meetingNumberInt ASC

// SpectraCQ RAN2_P2_CQ6-4 (RAN2, phase 2) -- CQ6
// Question: Return the trend of conclusion counts per meeting (study-closure trend).
// Gold: 11 rows, primary column "m.canonicalMeetingNumber"

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(c) AS conCount ORDER BY m.meetingNumberInt ASC

// SpectraCQ RAN5_P2_CQ6-1 (RAN5, phase 2) -- CQ6
// Question: Track resolution counts across meetings over time (resolution trend).
// Gold: 28 rows, primary column "meeting"

MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(r) AS cnt ORDER BY num ASC RETURN meeting, cnt

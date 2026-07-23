// SpectraCQ RAN5_P2_CQ6-2 (RAN5, phase 2) -- CQ6
// Question: Track Samsung's resolution contributions across meetings over time (contribution trend).
// Gold: 4 rows, primary column "meeting"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) WITH m.canonicalMeetingNumber AS meeting, m.meetingNumberInt AS num, count(DISTINCT r) AS cnt ORDER BY num ASC RETURN meeting, cnt

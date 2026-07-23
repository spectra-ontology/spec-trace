// SpectraCQ RAN4_P2_CQ6-2 (RAN4, phase 2) -- CQ6
// Question: Show how Samsung's resolution contributions evolved over time (contributor trend).
// Gold: 20 rows, primary column "m.canonicalMeetingNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(DISTINCT r) AS cnt ORDER BY mNum ASC

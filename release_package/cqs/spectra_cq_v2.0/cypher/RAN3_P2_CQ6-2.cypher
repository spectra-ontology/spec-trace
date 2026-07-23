// SpectraCQ RAN3_P2_CQ6-2 (RAN3, phase 2) -- CQ6
// Question: Show ZTE's resolution-contribution trend over time (influence trajectory).
// Gold: 30 rows, primary column "m.canonicalMeetingNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(DISTINCT r) AS cnt ORDER BY mNum ASC

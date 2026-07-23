// SpectraCQ RAN3_P2_CQ6-3 (RAN3, phase 2) -- CQ6
// Question: Show ZTE's moderator-role trend over time (leadership trajectory).
// Gold: 14 rows, primary column "m.canonicalMeetingNumber"

MATCH (s:Summary)-[:MODERATED_BY]->(c:Company {companyName: 'ZTE'}) MATCH (s)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt AS mNum, count(s) AS cnt ORDER BY mNum ASC

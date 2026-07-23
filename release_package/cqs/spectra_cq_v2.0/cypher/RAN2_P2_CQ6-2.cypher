// SpectraCQ RAN2_P2_CQ6-2 (RAN2, phase 2) -- CQ6
// Question: Track how Huawei's resolution-contribution rate changed over meetings (influence trend).
// Gold: 52 rows, primary column "m.canonicalMeetingNumber"

MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting) WITH m, count(r) AS total MATCH (r2:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (r2)-[:MADE_AT]->(m) WITH m, total, count(DISTINCT r2) AS huaweiCount RETURN m.canonicalMeetingNumber, m.meetingNumberInt, huaweiCount, total, round(100.0 * huaweiCount / total, 1) AS ratio ORDER BY m.meetingNumberInt ASC

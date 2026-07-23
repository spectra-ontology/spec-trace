// SpectraCQ RAN2_P2_CQ6-1 (RAN2, phase 2) -- CQ6
// Question: Return the trend of Rel-18 resolution counts over meetings (chronological trend).
// Gold: 20 rows, primary column "m.canonicalMeetingNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, m.meetingNumberInt, count(r) AS resCount ORDER BY m.meetingNumberInt ASC

// SpectraCQ RAN2_P2_CQ1-5 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the resolutions related to Rel-18 (release decision review).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}), (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, r.content ORDER BY m.meetingNumberInt DESC, r.sequence LIMIT 10

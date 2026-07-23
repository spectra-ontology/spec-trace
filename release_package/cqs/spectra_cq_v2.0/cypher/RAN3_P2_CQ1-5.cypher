// SpectraCQ RAN3_P2_CQ1-5 (RAN3, phase 2) -- CQ1_Resolution
// Question: List the resolutions tied to Rel-18 TDocs (release-scoped decision review).
// Gold: 15 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-18'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, r.resolutionId, t.tdocNumber LIMIT 15

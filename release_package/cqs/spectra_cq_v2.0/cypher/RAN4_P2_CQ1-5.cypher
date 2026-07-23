// SpectraCQ RAN4_P2_CQ1-5 (RAN4, phase 2) -- CQ1_Resolution
// Question: List the resolutions tied to Rel-15 TDocs (release-scoped decisions).
// Gold: 15 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release {releaseName: 'Rel-15'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15

// SpectraCQ RAN4_P2_CQ1-6 (RAN4, phase 2) -- CQ1_Resolution
// Question: List the resolutions that drive changes to spec 38.133 (decisions affecting a spec).
// Gold: 15 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT r.resolutionId, labels(r) AS types, m.canonicalMeetingNumber, m.meetingNumberInt AS mNum ORDER BY mNum DESC, r.resolutionId LIMIT 15

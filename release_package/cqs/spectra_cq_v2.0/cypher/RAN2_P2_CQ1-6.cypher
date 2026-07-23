// SpectraCQ RAN2_P2_CQ1-6 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the resolutions that drive changes to spec 38.331 (RRC decision impact).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}), (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, r.content ORDER BY m.meetingNumberInt DESC, r.resolutionId LIMIT 10

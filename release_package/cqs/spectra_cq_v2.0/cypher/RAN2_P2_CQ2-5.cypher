// SpectraCQ RAN2_P2_CQ2-5 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which resolutions did TDoc R2-2500064 lead to (contribution-to-decision trace)?
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R2-2500064'}), (r)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, r.resolutionId, labels(r) AS type, m.canonicalMeetingNumber, r.content

// SpectraCQ RAN2_P2_CQ2-1 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which resolutions did TDoc R2-2508373 lead to (contribution-to-decision trace)?
// Gold: 2 rows, primary column "t.tdocNumber"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WHERE 'R2-2508373' IN t.tdocNumber MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, r.resolutionId, labels(r) AS type, m.canonicalMeetingNumber, r.content

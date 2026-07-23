// SpectraCQ RAN2_P2_CQ2-4 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which specs were updated by agreed TDocs at RAN2#132 (spec-change trace)?
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec), (a)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN t.tdocNumber, sp.specNumber, a.resolutionId, a.content ORDER BY a.sequence, t.tdocNumber, sp.specNumber, a.resolutionId LIMIT 10

// SpectraCQ RAN1_P2_CQ2-3 (RAN1, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the agreements at meeting RAN1#115 that approved a CR (tracing spec-change decisions).
// Gold: 15 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved') RETURN a.resolutionId, a.content ORDER BY a.sequence, a.resolutionId LIMIT 15

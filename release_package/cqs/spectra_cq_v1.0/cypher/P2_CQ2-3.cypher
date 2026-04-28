// SpectraCQ P2_CQ2-3 — CQ2_Tdoc-Resolution추적
// Question (English): List Agreements at meeting RAN1#115 that approved CRs (spec-change decision tracing).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) WHERE a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved') RETURN a.resolutionId, a.content ORDER BY a.sequence LIMIT 15

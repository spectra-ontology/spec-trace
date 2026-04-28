// SpectraCQ P2_CQ5-11 — CQ5_기술트렌드
// Question (English): List Agreements about DMRS pattern (DMRS-pattern standardization).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DMRS' AND a.content CONTAINS 'pattern' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

// SpectraCQ P2_CQ5-1 — CQ5_기술트렌드
// Question (English): Return the chronological progression of Agreements about CSI-RS (technology-evolution tracing).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'CSI-RS' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt ASC LIMIT 15

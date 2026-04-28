// SpectraCQ P2_CQ5-2 — CQ5_기술트렌드
// Question (English): List Agreements about HARQ feedback (HARQ technical decisions).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'HARQ' AND a.content CONTAINS 'feedback' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

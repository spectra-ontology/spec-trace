// SpectraCQ P2_CQ5-13 — CQ5_기술트렌드
// Question (English): List Agreements about PUCCH resource.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUCCH' AND a.content CONTAINS 'resource' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

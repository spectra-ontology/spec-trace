// SpectraCQ P2_CQ5-8 — CQ5_기술트렌드
// Question (English): List Agreements about BWP switching.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'BWP' AND a.content CONTAINS 'switch' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

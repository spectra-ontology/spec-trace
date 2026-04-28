// SpectraCQ P2_CQ5-4 — CQ5_기술트렌드
// Question (English): List Agreements about DCI format (DCI-format standardization).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'DCI' AND a.content CONTAINS 'format' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

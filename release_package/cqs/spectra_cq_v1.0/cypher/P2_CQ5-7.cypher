// SpectraCQ P2_CQ5-7 — CQ5_기술트렌드
// Question (English): List Agreements about MIMO codebook.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'MIMO' AND a.content CONTAINS 'codebook' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

// SpectraCQ P2_CQ5-5 — CQ5_기술트렌드
// Question (English): List Agreements about PUSCH repetition (PUSCH-repetition technical decisions).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'repetition' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

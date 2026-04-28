// SpectraCQ P2_CQ5-12 — CQ5_기술트렌드
// Question (English): List Agreements about SSB burst set.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'SSB' AND a.content CONTAINS 'burst' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

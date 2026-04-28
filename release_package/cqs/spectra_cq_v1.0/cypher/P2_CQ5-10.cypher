// SpectraCQ P2_CQ5-10 — CQ5_기술트렌드
// Question (English): List Agreements about UCI multiplexing.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'UCI' AND a.content CONTAINS 'multiplex' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

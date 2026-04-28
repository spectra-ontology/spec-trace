// SpectraCQ P2_CQ5-9 — CQ5_기술트렌드
// Question (English): List Agreements about slot aggregation.
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'slot' AND a.content CONTAINS 'aggregation' RETURN m.meetingNumber, a.resolutionId, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

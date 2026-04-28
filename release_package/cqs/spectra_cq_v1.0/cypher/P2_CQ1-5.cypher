// SpectraCQ P2_CQ1-5 — CQ1_Resolution조회
// Question (English): List recent Agreements that contain FFS (For Further Study) markers (items needing additional review).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.hasFFS = true RETURN a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15

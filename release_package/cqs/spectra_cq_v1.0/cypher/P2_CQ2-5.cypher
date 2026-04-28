// SpectraCQ P2_CQ2-5 — CQ2_Tdoc-Resolution추적
// Question (English): List Resolutions related to TS 38.211 amendments (38.211 revision history).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS '38.211' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 15

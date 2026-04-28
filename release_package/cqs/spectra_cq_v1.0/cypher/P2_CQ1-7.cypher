// SpectraCQ P2_CQ1-7 — CQ1_Resolution조회
// Question (English): Return Agreements related to beam management (beam-management technical decisions).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'beam' AND (a.content CONTAINS 'management' OR a.content CONTAINS 'indication') RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

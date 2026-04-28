// SpectraCQ P2_CQ1-6 — CQ1_Resolution조회
// Question (English): Return Agreements related to PDCCH blind decoding (PDCCH technical-decision tracing).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PDCCH' AND a.content CONTAINS 'blind' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC LIMIT 10

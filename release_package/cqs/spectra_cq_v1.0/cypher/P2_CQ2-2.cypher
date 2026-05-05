// SpectraCQ P2_CQ2-2 — CQ2_Tdoc-Resolution추적
// Question (English): Identify which Agreement TDoc R1-2001110 led to (TDoc-to-standard outcome tracing).
// Schema area: classes=['Agreement', 'Meeting', 'Tdoc'], rels=['MADE_AT', 'REFERENCES']

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R1-2001110'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber

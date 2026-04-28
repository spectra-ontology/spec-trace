// SpectraCQ P4_CQ4-5 — CQ4_연계분석
// Question (English): Return aggregated change summaries for CRs agreed at RAN1#121 (the most-recent meeting with 18 CRs carrying summaryOfChange).
// Schema area: classes=['CR', 'Meeting', 'Resolution'], rels=['MADE_AT', 'REFERENCES']

MATCH (res:Resolution)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) MATCH (res)-[:REFERENCES]->(cr:CR) WHERE cr.summaryOfChange IS NOT NULL RETURN m.meetingNumber, res.resolutionId, cr.tdocNumber, cr.summaryOfChange ORDER BY cr.tdocNumber DESC LIMIT 15

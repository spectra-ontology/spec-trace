// SpectraCQ P3_CQ028 — Resolution_TS_의사결정
// Question (English): Return Resolutions on TS 38.213 mentioning HARQ (HARQ-related decision tracing).
// Schema area: classes=['CR', 'Meeting', 'Resolution', 'Spec'], rels=['MADE_AT', 'MODIFIES', 'REFERENCES']

MATCH (res:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE COALESCE(res.contentWithEquations, res.content, '') =~ '(?i).*HARQ.*' MATCH (res)-[:MADE_AT]->(m:Meeting) RETURN labels(res) AS type, res.resolutionId, COALESCE(res.contentWithEquations, res.content) AS content, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 10

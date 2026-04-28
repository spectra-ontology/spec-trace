// SpectraCQ P1_CQ1-4 — CQ1_Tdoc기본검색
// Question (English): List recently submitted TDocs targeting Release 18 (per-release contribution status).
// Schema area: classes=['Meeting', 'Release', 'Tdoc'], rels=['PRESENTED_AT', 'TARGET_RELEASE']

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.type, t.status, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

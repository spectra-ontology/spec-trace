// SpectraCQ RAN1_P1_CQ1-4 (RAN1, phase 1) -- CQ1_Tdoc
// Question: List the most recently submitted TDocs targeting Rel-18 (contribution status by release).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) MATCH (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.type, t.status, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

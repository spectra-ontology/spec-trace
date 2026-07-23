// SpectraCQ RAN2_P1_CQ1-4 (RAN2, phase 1) -- CQ1_Tdoc
// Question: List the most recently submitted TDocs targeting Rel-19 (latest Rel-19 activity).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-19'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.type, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

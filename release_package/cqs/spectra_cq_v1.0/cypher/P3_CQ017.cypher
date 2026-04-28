// SpectraCQ P3_CQ017 — CR_TS_변경추적
// Question (English): Return the 20 most recent CRs that modify TS 38.213.
// Schema area: classes=['CR', 'Company', 'Meeting', 'Spec'], rels=['MODIFIES', 'PRESENTED_AT', 'SUBMITTED_BY']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN cr.tdocNumber, cr.title, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 20

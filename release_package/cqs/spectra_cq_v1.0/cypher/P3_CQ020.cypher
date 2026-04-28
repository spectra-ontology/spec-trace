// SpectraCQ P3_CQ020 — CR_TS_변경추적
// Question (English): List CRs submitted by CompanyD against TS 38.214 (company-domain contribution).
// Schema area: classes=['CR', 'Company', 'Meeting', 'Spec'], rels=['MODIFIES', 'PRESENTED_AT', 'SUBMITTED_BY']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) WHERE co.companyName CONTAINS 'CompanyD' MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 20

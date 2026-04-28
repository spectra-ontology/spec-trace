// SpectraCQ P3_CQ018 — CR_TS_변경추적
// Question (English): Return CRs whose clausesAffected includes TS 38.214 §5.1 (impact on a specific section).
// Schema area: classes=['CR', 'Company', 'Meeting', 'Spec'], rels=['MODIFIES', 'PRESENTED_AT', 'SUBMITTED_BY']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS '5.1' MATCH (cr)-[:SUBMITTED_BY]->(co:Company) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, cr.clausesAffected, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15

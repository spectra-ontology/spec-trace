// SpectraCQ P3_CQ039 — 통합분석
// Question (English): Return the top-10 companies that submitted CRs against TS 38.214 (technical-leadership analysis).
// Schema area: classes=['CR', 'Company', 'Spec'], rels=['MODIFIES', 'SUBMITTED_BY']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10

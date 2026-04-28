// SpectraCQ P3_CQ037 — 통합분석
// Question (English): Return per-company CR submission counts across all 8 TSes (top contributors).
// Schema area: classes=['CR', 'Company', 'Spec'], rels=['MODIFIES', 'SUBMITTED_BY']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 15

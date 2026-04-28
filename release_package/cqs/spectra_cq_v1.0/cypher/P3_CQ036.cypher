// SpectraCQ P3_CQ036 — 통합분석
// Question (English): Return the top-5 TSes by CR count and their section counts (complexity vs amendment frequency).
// Schema area: classes=['CR', 'Section', 'Spec'], rels=['BELONGS_TO_SPEC', 'MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] WITH sp.specNumber AS ts, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5 MATCH (sec:Section)-[:BELONGS_TO_SPEC]->(sp2:Spec {specNumber: ts}) RETURN ts, crCount, count(sec) AS sectionCount ORDER BY crCount DESC

// SpectraCQ P1_CQ2-4 — CQ2_Tdoc관계추적
// Question (English): List the CRs that modify TS 38.214, with each CR's status (TS 38.214 amendment status).
// Schema area: classes=['Spec', 'Tdoc'], rels=['MODIFIES']

MATCH (t:Tdoc)-[:MODIFIES]->(s:Spec {specNumber: '38.214'}) WHERE t.type IN ['CR', 'draftCR'] RETURN t.tdocNumber, t.title, t.status, t.type ORDER BY t.tdocNumber ASC LIMIT 1

// SpectraCQ P2_CQ2-1 — CQ2_Tdoc-Resolution추적
// Question (English): List the TDocs referenced by Agreement AGR-100-6.1-001 (origin-document tracing for an approved CR).
// Schema area: classes=['Agreement', 'Tdoc'], rels=['REFERENCES']

MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title

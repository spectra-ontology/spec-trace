// SpectraCQ RAN1_P2_CQ2-1 (RAN1, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the TDocs referenced by Agreement AGR-100-6.1-001 (tracing the source documents behind a decision).
// Gold: 4 rows, primary column "a.resolutionId"

MATCH (a:Agreement {resolutionId: 'AGR-100-6.1-001'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title

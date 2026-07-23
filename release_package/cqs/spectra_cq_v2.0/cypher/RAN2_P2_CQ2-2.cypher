// SpectraCQ RAN2_P2_CQ2-2 (RAN2, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the TDocs referenced by Agreement AGR-132-8.13-005 (decision provenance).
// Gold: 2 rows, primary column "a.resolutionId"

MATCH (a:Agreement {resolutionId: 'AGR-132-8.13-005'})-[:REFERENCES]->(t:Tdoc) RETURN a.resolutionId, a.content, t.tdocNumber, t.title

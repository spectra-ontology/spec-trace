// SpectraCQ RAN4_P5_CQ2-5 (RAN4, phase 5) -- 
// Question: List the TRs that impacted spec 38.101-1 (reverse study lookup).
// Gold: 47 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.101-1'}) RETURN DISTINCT tr.trNumber, tr.trTitle, imp.impactType ORDER BY tr.trNumber

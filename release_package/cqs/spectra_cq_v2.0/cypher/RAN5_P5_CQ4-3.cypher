// SpectraCQ RAN5_P5_CQ4-3 (RAN5, phase 5) -- 
// Question: Which TRs impacted TS 38.533, with impact type? (spec-impact lookup)
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.533'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber

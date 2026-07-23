// SpectraCQ RAN5_P5_CQ2-4 (RAN5, phase 5) -- 
// Question: List the study-only TRs marked NoChange (no-spec-change studies).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NoChange'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber

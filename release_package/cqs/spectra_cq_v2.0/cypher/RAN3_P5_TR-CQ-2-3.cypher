// SpectraCQ RAN3_P5_TR-CQ-2-3 (RAN3, phase 5) -- 
// Question: List the TRs whose impact type is NewTS (new-spec-producing studies).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle

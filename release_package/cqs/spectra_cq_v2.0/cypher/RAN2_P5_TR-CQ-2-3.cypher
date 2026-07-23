// SpectraCQ RAN2_P5_TR-CQ-2-3 (RAN2, phase 5) -- 
// Question: List the TRs that spawned a new TS (new-spec studies).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'NewTS'
                  RETURN DISTINCT tr.trNumber, tr.trTitle

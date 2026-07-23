// SpectraCQ RAN2_P5_TR-CQ-2-4 (RAN2, phase 5) -- 
// Question: List the TRs that extend existing sections (section-extension studies).
// Gold: 6 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle

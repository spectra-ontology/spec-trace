// SpectraCQ RAN3_P5_TR-CQ-2-4 (RAN3, phase 5) -- 
// Question: List the TRs whose impact type is ExtendSection (section-extending studies).
// Gold: 8 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  WHERE imp.impactType = 'ExtendSection'
                  RETURN DISTINCT tr.trNumber, tr.trTitle

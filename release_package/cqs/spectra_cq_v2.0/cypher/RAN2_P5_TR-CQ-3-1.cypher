// SpectraCQ RAN2_P5_TR-CQ-3-1 (RAN2, phase 5) -- 
// Question: Which specs does TR 38.825 impact, and how (impact detail)?
// Gold: 2 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription

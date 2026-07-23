// SpectraCQ RAN2_P5_TR-CQ-3-3 (RAN2, phase 5) -- 
// Question: Return TR 38.874's impact on spec 38.300 (targeted impact).
// Gold: 1 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.874'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN imp.impactType, imp.impactDescription

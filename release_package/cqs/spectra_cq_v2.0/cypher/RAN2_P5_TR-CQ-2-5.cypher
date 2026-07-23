// SpectraCQ RAN2_P5_TR-CQ-2-5 (RAN2, phase 5) -- 
// Question: Which TRs impacted spec 38.300 (reverse impact lookup)?
// Gold: 5 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.300'})
                  RETURN tr.trNumber, imp.impactType

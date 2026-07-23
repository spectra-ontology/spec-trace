// SpectraCQ RAN2_P5_TR-CQ-3-2 (RAN2, phase 5) -- 
// Question: Return TR 38.836's impact on specs 38.300 and 38.321 (targeted impact).
// Gold: 2 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.836'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  WHERE s.specNumber IN ['38.300', '38.321']
                  RETURN s.specNumber, imp.impactType, imp.impactDescription

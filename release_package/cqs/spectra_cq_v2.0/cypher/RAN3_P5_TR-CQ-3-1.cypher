// SpectraCQ RAN3_P5_TR-CQ-3-1 (RAN3, phase 5) -- 
// Question: Return which specs TR 38.823 impacts, with impact type and description (study-impact detail).
// Gold: 6 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType, imp.impactDescription

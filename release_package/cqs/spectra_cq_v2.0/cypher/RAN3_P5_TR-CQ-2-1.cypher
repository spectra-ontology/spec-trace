// SpectraCQ RAN3_P5_TR-CQ-2-1 (RAN3, phase 5) -- 
// Question: List the specs impacted by TR 38.823 (study-to-spec impact).
// Gold: 6 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.823'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType

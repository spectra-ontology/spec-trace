// SpectraCQ RAN4_P5_CQ2-1 (RAN4, phase 5) -- 
// Question: List the specs impacted by TR 38.803 (study-to-spec impact).
// Gold: 4 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber

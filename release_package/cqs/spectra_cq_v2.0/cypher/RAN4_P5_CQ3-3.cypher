// SpectraCQ RAN4_P5_CQ3-3 (RAN4, phase 5) -- 
// Question: What spec impact, with details, did the NTN RF study TR 38.863 have? (study-to-spec impact detail).
// Gold: 1 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.863'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber

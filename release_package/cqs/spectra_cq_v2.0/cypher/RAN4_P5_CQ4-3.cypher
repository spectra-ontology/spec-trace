// SpectraCQ RAN4_P5_CQ4-3 (RAN4, phase 5) -- 
// Question: Return the conclusions of RedCap RF study TR 38.860 and how they were reflected in specs (study-to-spec outcome).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.860'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.conclusions, s.specNumber, imp.impactType

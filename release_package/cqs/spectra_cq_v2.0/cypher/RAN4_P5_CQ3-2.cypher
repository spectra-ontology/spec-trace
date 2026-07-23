// SpectraCQ RAN4_P5_CQ3-2 (RAN4, phase 5) -- 
// Question: What spec impact did the FR2 extension study TR 38.820 have? (study-to-spec impact).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.820'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, tr.trStatus, s.specNumber, imp.impactType

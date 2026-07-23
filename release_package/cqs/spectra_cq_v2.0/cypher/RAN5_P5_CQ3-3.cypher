// SpectraCQ RAN5_P5_CQ3-3 (RAN5, phase 5) -- 
// Question: Report the study findings of TR 38.918 (NoChange outcome).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.918'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, tr.trTitle, imp.impactType, imp.impactDescription

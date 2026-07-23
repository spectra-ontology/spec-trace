// SpectraCQ RAN1_P5_CQ4-3 (RAN1, phase 5) -- CQ4
// Question: Return the conclusions of TR 38.808 (52.6-71 GHz band) and how they were reflected into the TSs (mmWave product planning).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.808'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions, ti.impactType, sp.specNumber

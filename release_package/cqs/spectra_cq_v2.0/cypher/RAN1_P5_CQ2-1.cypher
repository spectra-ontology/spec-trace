// SpectraCQ RAN1_P5_CQ2-1 (RAN1, phase 5) -- CQ2_TS
// Question: Did the Ambient IoT study (TR 38.769) create any new TS? If so, which TS and what impact type?
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.769'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, tr.trTitle, ti.impactType, sp.specNumber, ti.impactDescription

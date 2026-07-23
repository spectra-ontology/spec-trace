// SpectraCQ RAN1_P5_CQ3-3 (RAN1, phase 5) -- CQ3
// Question: What impact did the URLLC study TR 38.824 have on TS 38.211 and 38.214, in detail? (low-latency industrial comms)
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.824'})-[:HAS_TR_IMPACT]->(ti:TRImpact)-[:IMPACTS_SPEC]->(sp:Spec) RETURN tr.trNumber, sp.specNumber, ti.impactType, ti.affectedSection, ti.impactDescription ORDER BY sp.specNumber

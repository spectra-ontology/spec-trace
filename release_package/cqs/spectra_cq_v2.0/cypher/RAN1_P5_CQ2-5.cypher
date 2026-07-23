// SpectraCQ RAN1_P5_CQ2-5 (RAN1, phase 5) -- CQ2_TS
// Question: List the TR studies that spawned an entirely new TS, with the resulting TS number (origins of new specs).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(ti:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(sp:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, sp.specNumber, ti.impactDescription ORDER BY tr.trNumber

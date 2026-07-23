// SpectraCQ RAN4_P5_CQ2-3 (RAN4, phase 5) -- 
// Question: Which TRs led to a new TS? (spinning up new specs).
// Gold: 4 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'NewTS'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber, tr.trTitle, s.specNumber ORDER BY tr.trNumber

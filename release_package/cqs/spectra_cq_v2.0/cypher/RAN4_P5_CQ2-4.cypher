// SpectraCQ RAN4_P5_CQ2-4 (RAN4, phase 5) -- 
// Question: Which TRs extended existing spec sections? (incremental spec impact).
// Gold: 20 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'})-[:IMPACTS_SPEC]->(s:Spec) RETURN DISTINCT tr.trNumber, s.specNumber ORDER BY tr.trNumber LIMIT 20

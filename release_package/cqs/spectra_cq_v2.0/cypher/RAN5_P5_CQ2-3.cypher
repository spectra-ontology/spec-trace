// SpectraCQ RAN5_P5_CQ2-3 (RAN5, phase 5) -- 
// Question: Which TRs impacted specs by extending sections? (ExtendSection impact filter)
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact {impactType: 'ExtendSection'}) RETURN DISTINCT tr.trNumber, tr.trTitle ORDER BY tr.trNumber

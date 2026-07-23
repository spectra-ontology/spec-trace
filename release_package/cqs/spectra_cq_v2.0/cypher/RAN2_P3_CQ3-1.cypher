// SpectraCQ RAN2_P3_CQ3-1 (RAN2, phase 3) -- CQ3_CR
// Question: Which spec does CR R2-2509337 modify (change target)?
// Gold: 1 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE cr.tdocNumber = 'R2-2509337' RETURN sp.specNumber

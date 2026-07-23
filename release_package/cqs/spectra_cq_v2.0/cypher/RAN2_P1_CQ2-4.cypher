// SpectraCQ RAN2_P1_CQ2-4 (RAN2, phase 1) -- CQ2_Tdoc
// Question: Which spec does CR R2-2509337 modify (change target)?
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:MODIFIES]->(s:Spec) RETURN t.tdocNumber, t.title, s.specNumber, s.specVersion LIMIT 1

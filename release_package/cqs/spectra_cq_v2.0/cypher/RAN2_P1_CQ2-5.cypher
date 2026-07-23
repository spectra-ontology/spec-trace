// SpectraCQ RAN2_P1_CQ2-5 (RAN2, phase 1) -- CQ2_Tdoc
// Question: Return the change category and affected scope of CR R2-2509337 (impact assessment).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.crCategory, t.clausesAffected, t.affectsUICC, t.affectsME, t.affectsRAN, t.affectsCN LIMIT 1

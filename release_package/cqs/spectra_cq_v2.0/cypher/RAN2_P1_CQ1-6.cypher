// SpectraCQ RAN2_P1_CQ1-6 (RAN2, phase 1) -- CQ1_Tdoc
// Question: Return the decision status of TDoc R2-2509337 (outcome lookup).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.status, t.type LIMIT 1

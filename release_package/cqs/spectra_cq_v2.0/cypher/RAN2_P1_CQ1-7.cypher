// SpectraCQ RAN2_P1_CQ1-7 (RAN2, phase 1) -- CQ1_Tdoc
// Question: Return the intended purpose (the 'For' field) of TDoc R2-2509337 (contribution intent).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509337'}) RETURN t.tdocNumber, t.title, t.`for` LIMIT 1

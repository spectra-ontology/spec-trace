// SpectraCQ RAN3_P1_CQ1-7 (RAN3, phase 1) -- CQ1_Tdoc
// Question: Return the 'For' purpose of TDoc R3-258530 (identifying document intent).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.for

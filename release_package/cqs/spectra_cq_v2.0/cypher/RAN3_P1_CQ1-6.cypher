// SpectraCQ RAN3_P1_CQ1-6 (RAN3, phase 1) -- CQ1_Tdoc
// Question: Return the decision status of TDoc R3-258530 (checking the outcome).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-258530'}) RETURN t.tdocNumber, t.status, t.type

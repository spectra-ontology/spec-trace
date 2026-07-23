// SpectraCQ RAN1_P1_CQ1-7 (RAN1, phase 1) -- CQ1_Tdoc
// Question: What is the intended purpose (For) of TDoc R1-2501234 — Discussion, Approval, or Agreement?
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.for LIMIT 1

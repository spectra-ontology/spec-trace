// SpectraCQ RAN1_P1_CQ1-6 (RAN1, phase 1) -- CQ1_Tdoc
// Question: What is the final status of TDoc R1-2501234? (single-document status lookup)
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.status LIMIT 1

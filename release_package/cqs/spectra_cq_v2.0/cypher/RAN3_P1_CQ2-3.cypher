// SpectraCQ RAN3_P1_CQ2-3 (RAN3, phase 1) -- CQ2_Tdoc
// Question: Return the LS that TDoc R3-241518 replies to (liaison reply linkage).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-241518'})-[:REPLY_TO]->(orig:Tdoc) RETURN t.tdocNumber, orig.tdocNumber, orig.title

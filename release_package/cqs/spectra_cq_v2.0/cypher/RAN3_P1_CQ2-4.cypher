// SpectraCQ RAN3_P1_CQ2-4 (RAN3, phase 1) -- CQ2_Tdoc
// Question: Return the specs that CR R3-258530 modifies (change-impact scope).
// Gold: 1 rows, primary column "c.tdocNumber"

MATCH (c:CR {tdocNumber: 'R3-258530'})-[:MODIFIES]->(s:Spec) RETURN c.tdocNumber, s.specNumber

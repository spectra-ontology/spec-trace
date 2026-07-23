// SpectraCQ RAN1_P1_CQ1-8 (RAN1, phase 1) -- CQ1_Tdoc
// Question: Who is the contact person for TDoc R1-2501234? (contact lookup)
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R1-2501234'})-[:HAS_CONTACT]->(ct:Contact) RETURN t.tdocNumber, ct.contactName LIMIT 1

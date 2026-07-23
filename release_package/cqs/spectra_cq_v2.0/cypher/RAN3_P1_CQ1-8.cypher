// SpectraCQ RAN3_P1_CQ1-8 (RAN3, phase 1) -- CQ1_Tdoc
// Question: Return the contact person for TDoc R3-258530 (finding the responsible author).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId

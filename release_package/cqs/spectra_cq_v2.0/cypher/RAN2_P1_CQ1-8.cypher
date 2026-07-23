// SpectraCQ RAN2_P1_CQ1-8 (RAN2, phase 1) -- CQ1_Tdoc
// Question: Return the contact person for TDoc R2-2509337 (author follow-up).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509337'})-[:HAS_CONTACT]->(c:Contact) RETURN t.tdocNumber, c.contactName, c.contactId LIMIT 1

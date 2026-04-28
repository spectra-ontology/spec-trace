// SpectraCQ P1_CQ1-8 — CQ1_Tdoc기본검색
// Question (English): Return the contact (submitter contact) of TDoc R1-2599001.
// Schema area: classes=['Contact', 'Tdoc'], rels=['HAS_CONTACT']

MATCH (t:Tdoc {tdocNumber: 'R1-2599001'})-[:HAS_CONTACT]->(ct:Contact) RETURN t.tdocNumber, ct.contactName LIMIT 1

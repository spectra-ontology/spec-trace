// SpectraCQ P2_CQ3-6 — CQ3_company_contribution
// Question (English): List Apple's TDocs that reached approved status.
// Schema area: classes=['Company', 'Tdoc'], rels=['SUBMITTED_BY']

MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber DESC LIMIT 15

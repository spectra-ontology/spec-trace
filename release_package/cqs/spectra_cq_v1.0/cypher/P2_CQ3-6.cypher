// SpectraCQ P2_CQ3-6 — CQ3_회사기여도
// Question (English): List Samsung's TDocs that reached approved status.
// Schema area: classes=['Company', 'Tdoc'], rels=['SUBMITTED_BY']

MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber DESC LIMIT 15

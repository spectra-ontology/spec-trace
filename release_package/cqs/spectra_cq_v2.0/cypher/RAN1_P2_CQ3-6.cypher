// SpectraCQ RAN1_P2_CQ3-6 (RAN1, phase 2) -- CQ3
// Question: Which of ZTE's TDocs were approved? (approval track record)
// Gold: 15 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {status: 'approved'})-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber DESC LIMIT 15

// SpectraCQ RAN4_P1_CQ1-2 (RAN4, phase 1) -- 
// Question: Return the details of TDoc R4-2417515, including its submitting company (document lookup).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber:'R4-2417515'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, t.type, c.companyName

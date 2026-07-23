// SpectraCQ RAN5_P1_CQ1-2 (RAN5, phase 1) -- 
// Question: Return the details of TDoc R5-255500, including its submitting company (document lookup).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber:'R5-255500'}) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN t.tdocNumber, t.title, t.type, c.companyName

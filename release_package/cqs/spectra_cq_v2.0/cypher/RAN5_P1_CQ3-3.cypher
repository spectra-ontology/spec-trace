// SpectraCQ RAN5_P1_CQ3-3 (RAN5, phase 1) -- 
// Question: Which ten companies submitted the most CRs? (contribution ranking)
// Gold: 10 rows, primary column "c.companyName"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10

// SpectraCQ RAN4_P1_CQ3-3 (RAN4, phase 1) -- 
// Question: List the top 10 companies by CR contributions (leading CR contributors).
// Gold: 10 rows, primary column "c.companyName"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(cr) AS cnt ORDER BY cnt DESC LIMIT 10

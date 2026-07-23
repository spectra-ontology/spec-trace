// SpectraCQ RAN3_P2_CQ4-3 (RAN3, phase 2) -- CQ4_Moderator
// Question: Return the top 10 companies by moderator assignments (leadership distribution).
// Gold: 10 rows, primary column "c.companyName"

MATCH (s:Summary)-[:MODERATED_BY]->(c:Company) RETURN c.companyName, count(s) AS cnt ORDER BY cnt DESC, c.companyName ASC LIMIT 10

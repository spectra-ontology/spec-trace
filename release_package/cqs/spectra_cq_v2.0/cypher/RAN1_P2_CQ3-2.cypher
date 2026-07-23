// SpectraCQ RAN1_P2_CQ3-2 (RAN1, phase 2) -- CQ3
// Question: How many of Samsung's TDocs fed into agreements, and what share? (contribution performance)
// Gold: 1 rows, primary column "c.companyName"

MATCH (c:Company {companyName: 'Samsung'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH c, count(t) AS totalTdocs OPTIONAL MATCH (a:Agreement)-[:REFERENCES]->(t2:Tdoc)-[:SUBMITTED_BY]->(c) WITH c, totalTdocs, count(DISTINCT a) AS agreementCount RETURN c.companyName, totalTdocs, agreementCount, round(100.0 * agreementCount / totalTdocs, 1) AS contributionRate

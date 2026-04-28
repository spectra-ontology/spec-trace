// SpectraCQ P2_CQ3-2 — CQ3_회사기여도
// Question (English): Return CompanyE's Agreement-contributing TDoc count and ratio (standard-contribution analysis).
// Schema area: classes=['Agreement', 'Company', 'Tdoc'], rels=['REFERENCES', 'SUBMITTED_BY']

MATCH (c:Company {companyName: 'CompanyE'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH c, count(t) AS totalTdocs OPTIONAL MATCH (a:Agreement)-[:REFERENCES]->(t2:Tdoc)-[:SUBMITTED_BY]->(c) WITH c, totalTdocs, count(DISTINCT a) AS agreementCount RETURN c.companyName, totalTdocs, agreementCount, round(100.0 * agreementCount / totalTdocs, 1) AS contributionRate

// SpectraCQ P2_CQ3-5 — CQ3_회사기여도
// Question (English): Compare Ericsson's and HiSilicon's Resolution contributions.
// Schema area: classes=['Agreement', 'Company', 'Tdoc'], rels=['REFERENCES', 'SUBMITTED_BY']

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE c.companyName IN ['Ericsson', 'HiSilicon'] RETURN c.companyName, count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC

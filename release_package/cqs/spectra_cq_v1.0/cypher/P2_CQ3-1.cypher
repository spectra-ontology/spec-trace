// SpectraCQ P2_CQ3-1 — CQ3_회사기여도
// Question (English): List TDocs from CompanyA that led to Agreements (company-level standard-contribution tracing).
// Schema area: classes=['Agreement', 'Company', 'Meeting', 'Tdoc'], rels=['MADE_AT', 'REFERENCES', 'SUBMITTED_BY']

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'CompanyA'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, a.resolutionId, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 15

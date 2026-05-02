// SpectraCQ P2_CQ3-4 — CQ3_회사기여도
// Question (English): Return Qualcomm's 10 most recent Agreement-participating TDocs.
// Schema area: classes=['Agreement', 'Company', 'Meeting', 'Tdoc'], rels=['MADE_AT', 'REFERENCES', 'SUBMITTED_BY']

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Qualcomm'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 10

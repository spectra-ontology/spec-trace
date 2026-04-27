// P1_CQ1-3 — Phase 1 (Tdoc metadata)
// List the Tdocs presented at meeting RAN1#120 submitted by a given Company (replace 'CompanyX' with an actual vendor name from your knowledge graph).

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'CompanyX'}) RETURN t.tdocNumber, t.title, t.type, t.status ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10

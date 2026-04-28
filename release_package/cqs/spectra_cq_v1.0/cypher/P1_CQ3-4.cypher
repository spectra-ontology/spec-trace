// SpectraCQ P1_CQ3-4 — CQ3_회사분석
// Question (English): Return the count and ratio of TDocs submitted by CompanyD that reached approved/agreed status (company-level outcome analysis).
// Schema area: classes=['Company', 'Tdoc'], rels=['SUBMITTED_BY']

MATCH (c:Company {companyName: 'CompanyD'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, round(100.0 * approved / total, 1) AS approvalRate LIMIT 10

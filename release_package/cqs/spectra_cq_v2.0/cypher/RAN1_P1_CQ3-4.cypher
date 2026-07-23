// SpectraCQ RAN1_P1_CQ3-4 (RAN1, phase 1) -- CQ3
// Question: What share and count of Qualcomm's TDocs were approved or agreed? (contribution success rate)
// Gold: 1 rows, primary column "total"

MATCH (c:Company {companyName: 'Qualcomm'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS total, sum(CASE WHEN t.status IN ['approved', 'agreed'] THEN 1 ELSE 0 END) AS approved RETURN total, approved, round(100.0 * approved / total, 1) AS approvalRate LIMIT 10

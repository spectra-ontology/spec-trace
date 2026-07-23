// SpectraCQ RAN2_P2_CQ3-1 (RAN2, phase 2) -- CQ3
// Question: Return the share of Huawei's TDocs that led to resolutions (effectiveness rate).
// Gold: 1 rows, primary column "totalTdocs"

MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(t:Tdoc) WITH count(t) AS totalTdocs MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(t:Tdoc)<-[:REFERENCES]-(r:Resolution) WITH totalTdocs, count(DISTINCT t) AS resolvedTdocs RETURN totalTdocs, resolvedTdocs, round(100.0 * resolvedTdocs / totalTdocs, 1) AS ratio

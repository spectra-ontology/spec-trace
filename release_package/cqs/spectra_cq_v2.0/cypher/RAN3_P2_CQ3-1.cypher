// SpectraCQ RAN3_P2_CQ3-1 (RAN3, phase 2) -- CQ3
// Question: Return how many of ZTE's TDocs led to resolutions (contribution effectiveness).
// Gold: 1 rows, primary column "totalTdocs"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'ZTE'}) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(t) RETURN count(DISTINCT t) AS totalTdocs, count(DISTINCT r) AS resolutionLinkedTdocs

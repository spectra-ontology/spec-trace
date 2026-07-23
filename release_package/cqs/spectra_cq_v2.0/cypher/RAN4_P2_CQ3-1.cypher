// SpectraCQ RAN4_P2_CQ3-1 (RAN4, phase 2) -- CQ3
// Question: What share of Samsung's TDocs led to resolutions? (contribution success rate).
// Gold: 1 rows, primary column "totalTdocs"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) OPTIONAL MATCH (r:Resolution)-[:REFERENCES]->(t) RETURN count(DISTINCT t) AS totalTdocs, count(DISTINCT r) AS resolutionLinkedTdocs

// SpectraCQ RAN4_P4_CQ4-2 (RAN4, phase 4) -- CQ4
// Question: Return the reason and summary of change for CRs approved by agreements (decision-linked change review).
// Gold: 5 rows, primary column "tdocNumber"

MATCH (a:Agreement)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary

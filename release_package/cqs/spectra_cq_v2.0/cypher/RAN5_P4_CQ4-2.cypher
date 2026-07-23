// SpectraCQ RAN5_P4_CQ4-2 (RAN5, phase 4) -- CQ4
// Question: For CRs referenced by a conclusion, give their change reason and summary (decision-linked rationale).
// Gold: 5 rows, primary column "tdocNumber"

MATCH (con:Conclusion)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5 RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary

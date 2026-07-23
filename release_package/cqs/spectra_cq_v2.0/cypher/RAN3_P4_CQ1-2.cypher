// SpectraCQ RAN3_P4_CQ1-2 (RAN3, phase 4) -- CQ1
// Question: Return the summary-of-change of CR R3-237113 (change-content review).
// Gold: 1 rows, primary column "summaryOfChange"

MATCH (c:CR {tdocNumber: 'R3-237113'}) RETURN c.summaryOfChange AS summaryOfChange LIMIT 1

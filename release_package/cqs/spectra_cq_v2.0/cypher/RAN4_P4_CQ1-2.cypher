// SpectraCQ RAN4_P4_CQ1-2 (RAN4, phase 4) -- CQ1
// Question: Return the summary-of-change of CR R4-2107689 (change summary review).
// Gold: 1 rows, primary column "summaryOfChange"

MATCH (c:CR {tdocNumber: 'R4-2107689'}) RETURN c.summaryOfChange AS summaryOfChange LIMIT 1

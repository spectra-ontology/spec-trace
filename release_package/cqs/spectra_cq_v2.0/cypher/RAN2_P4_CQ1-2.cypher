// SpectraCQ RAN2_P4_CQ1-2 (RAN2, phase 4) -- CQ1
// Question: Return the summary of change of CR R2-2508534 (change overview).
// Gold: 1 rows, primary column "summaryOfChange"

MATCH (c:CR {tdocNumber: 'R2-2508534'}) RETURN c.summaryOfChange AS summaryOfChange LIMIT 1

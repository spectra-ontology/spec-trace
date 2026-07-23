// SpectraCQ RAN5_P4_CQ1-2 (RAN5, phase 4) -- CQ1
// Question: Give the summary-of-change of CR R5-261671 (change overview).
// Gold: 1 rows, primary column "summaryOfChange"

MATCH (c:CR {tdocNumber: 'R5-261671'}) RETURN c.summaryOfChange AS summaryOfChange LIMIT 1

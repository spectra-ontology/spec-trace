// SpectraCQ RAN1_P4_CQ1-2 (RAN1, phase 4) -- CQ1_CR
// Question: What is the summary-of-change of CR R1-2506685, introducing the Rel-19 UL Tx switching 3Tx UE scenario?
// Gold: 1 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber: 'R1-2506685'}) WHERE cr.summaryOfChange IS NOT NULL RETURN cr.tdocNumber, cr.summaryOfChange

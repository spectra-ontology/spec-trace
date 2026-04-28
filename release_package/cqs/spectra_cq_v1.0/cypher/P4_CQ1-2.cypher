// SpectraCQ P4_CQ1-2 — CQ1_CR변경근거
// Question (English): Return the summary-of-change of CR R1-2506685 (Rel-19 UL Tx switching 3Tx UE scenario).
// Schema area: classes=['CR'], rels=[]

MATCH (cr:CR {tdocNumber: 'R1-2506685'}) WHERE cr.summaryOfChange IS NOT NULL RETURN cr.tdocNumber, cr.summaryOfChange

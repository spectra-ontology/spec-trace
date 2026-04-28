// SpectraCQ P4_CQ1-1 — CQ1_CR변경근거
// Question (English): Return the reason-for-change of CR R1-2504971 (which affects 5 specs for the LP-WUS/WUR adoption).
// Schema area: classes=['CR'], rels=[]

MATCH (cr:CR {tdocNumber: 'R1-2504971'}) WHERE cr.reasonForChange IS NOT NULL RETURN cr.tdocNumber, cr.reasonForChange

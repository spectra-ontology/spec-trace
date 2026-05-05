// SpectraCQ P1_CQ1-6 — CQ1_Tdoc_basic_lookup
// Question (English): Return the decision status of TDoc R1-2501234 (single-TDoc status lookup).
// Schema area: classes=['Tdoc'], rels=[]

MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.status LIMIT 1

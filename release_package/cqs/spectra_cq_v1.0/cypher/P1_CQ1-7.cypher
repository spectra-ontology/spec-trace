// SpectraCQ P1_CQ1-7 — CQ1_Tdoc기본검색
// Question (English): Return the purpose (For field, e.g., Discussion/Approval/Agreement) of TDoc R1-2501234.
// Schema area: classes=['Tdoc'], rels=[]

MATCH (t:Tdoc {tdocNumber: 'R1-2501234'}) RETURN t.tdocNumber, t.title, t.for LIMIT 1

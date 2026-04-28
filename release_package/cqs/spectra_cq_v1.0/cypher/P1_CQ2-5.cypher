// SpectraCQ P1_CQ2-5 — CQ2_Tdoc관계추적
// Question (English): Return the CR category (F/A/B/C/D) and the affected clauses for CR R1-2599971.
// Schema area: classes=['Tdoc'], rels=[]

MATCH (t:Tdoc {tdocNumber: 'R1-2599971'}) RETURN t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status LIMIT 1

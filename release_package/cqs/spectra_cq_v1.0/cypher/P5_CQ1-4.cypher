// SpectraCQ P5_CQ1-4 — CQ1_TR연구현황분석
// Question (English): Return the scope and conclusions of TR 38.885 (V2X Sidelink) — automotive-communications product planning.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trNumber: '38.885'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions

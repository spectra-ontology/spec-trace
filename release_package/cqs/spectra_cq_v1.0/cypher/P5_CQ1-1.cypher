// SpectraCQ P5_CQ1-1 — CQ1_TR연구현황분석
// Question (English): Return the scope and conclusions of TR 38.769 (Ambient IoT for NR) — required for new IoT product planning.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trNumber: '38.769'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions

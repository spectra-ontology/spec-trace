// SpectraCQ P5_CQ1-2 — CQ1_TR연구현황분석
// Question (English): Return the trStatus and conclusions of TR 38.889 (NR-U) to assess standardization readiness.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions

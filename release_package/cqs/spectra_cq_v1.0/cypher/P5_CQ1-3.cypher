// SpectraCQ P5_CQ1-3 — CQ1_TR연구현황분석
// Question (English): List TRs currently in Draft status to forecast upcoming standard impact.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber

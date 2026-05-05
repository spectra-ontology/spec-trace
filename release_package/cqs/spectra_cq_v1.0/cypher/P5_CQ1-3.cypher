// SpectraCQ P5_CQ1-3 — CQ1_TR_study_status_analysis
// Question (English): List TRs currently in Draft status to forecast upcoming standard impact.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trStatus: 'Draft'}) RETURN tr.trNumber, tr.trTitle, tr.scope ORDER BY tr.trNumber

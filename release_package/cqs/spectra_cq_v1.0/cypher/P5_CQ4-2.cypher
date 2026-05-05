// SpectraCQ P5_CQ4-2 — CQ4_per_release_research_impact
// Question (English): Return the trStatus and scope of TR 38.760-1 (6G Radio) — next-generation roadmap review.
// Schema area: classes=['TechnicalReport'], rels=[]

MATCH (tr:TechnicalReport {trNumber: '38.760-1'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.trVersion, tr.scope

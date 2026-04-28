// SpectraCQ P5_CQ5-2 — CQ5_TR간참조관계
// Question (English): Return TRs that reference TR 38.802 (RedCap) — reverse reference, follow-up research tracking.
// Schema area: classes=['TechnicalReport'], rels=['REFERENCES_TR']

MATCH (tr:TechnicalReport {trNumber: '38.802'})<-[:REFERENCES_TR]-(src:TechnicalReport) RETURN tr.trNumber, tr.trTitle, src.trNumber, src.trTitle ORDER BY src.trNumber

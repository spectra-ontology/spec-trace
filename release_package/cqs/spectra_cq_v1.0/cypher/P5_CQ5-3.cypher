// SpectraCQ P5_CQ5-3 — CQ5_TR간참조관계
// Question (English): Return the top-5 most-referenced TRs (core-foundation research identification).
// Schema area: classes=['TechnicalReport'], rels=['REFERENCES_TR']

MATCH (ref:TechnicalReport)<-[:REFERENCES_TR]-(src:TechnicalReport) WITH ref, count(src) AS refCount ORDER BY refCount DESC LIMIT 5 RETURN ref.trNumber, ref.trTitle, refCount

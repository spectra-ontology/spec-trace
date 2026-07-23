// SpectraCQ RAN1_P5_CQ5-3 (RAN1, phase 5) -- CQ5_TR
// Question: Which are the top 5 most-referenced TRs? (identifying foundational studies)
// Gold: 5 rows, primary column "ref.trNumber"

MATCH (ref:TechnicalReport)<-[:REFERENCES_TR]-(src:TechnicalReport) WITH ref, count(src) AS refCount ORDER BY refCount DESC, ref.trNumber LIMIT 5 RETURN ref.trNumber, ref.trTitle, refCount

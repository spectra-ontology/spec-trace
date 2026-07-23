// SpectraCQ RAN4_P5_CQ5-3 (RAN4, phase 5) -- 
// Question: List the top 5 most-referenced TRs (most-cited studies).
// Gold: 5 rows, primary column "tr.trNumber"

MATCH (ref:TechnicalReport)-[:REFERENCES_TR]->(tr:TechnicalReport) WITH tr, count(ref) AS refCount RETURN tr.trNumber, tr.trTitle, refCount ORDER BY refCount DESC, tr.trNumber LIMIT 5

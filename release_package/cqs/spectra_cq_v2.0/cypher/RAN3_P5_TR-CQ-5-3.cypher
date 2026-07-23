// SpectraCQ RAN3_P5_TR-CQ-5-3 (RAN3, phase 5) -- 
// Question: Return the top 5 TRs by number of spec impacts (highest-impact studies).
// Gold: 5 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN tr.trNumber, count(imp) AS cnt ORDER BY cnt DESC, tr.trNumber LIMIT 5

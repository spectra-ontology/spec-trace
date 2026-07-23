// SpectraCQ RAN3_P5_TR-CQ-1-4 (RAN3, phase 5) -- 
// Question: Show the status distribution across all TRs (study-progress overview).
// Gold: 2 rows, primary column "tr.trStatus"

MATCH (tr:TechnicalReport) RETURN tr.trStatus, count(tr) AS cnt ORDER BY cnt DESC

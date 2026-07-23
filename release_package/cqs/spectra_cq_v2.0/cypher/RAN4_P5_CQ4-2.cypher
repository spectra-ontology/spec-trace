// SpectraCQ RAN4_P5_CQ4-2 (RAN4, phase 5) -- 
// Question: Return the status and scope of the IAB RF study TR 38.809 (study progress check).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.809'}) RETURN tr.trNumber, tr.trStatus, tr.scope

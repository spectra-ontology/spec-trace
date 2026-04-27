// P5_CQ1-2 — Phase 5 (TR study status)
// Return the trStatus and conclusions of TR 38.889.

MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.conclusions

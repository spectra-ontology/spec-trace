// P5_CQ1-1 — Phase 5 (TR study status)
// Return the trStatus, scope, and conclusions of TR 38.769.

MATCH (tr:TechnicalReport {trNumber: '38.769'}) RETURN tr.trNumber, tr.trTitle, tr.trStatus, tr.scope, tr.conclusions

// P4_CQ1-2 — Phase 4 (CR rationale)
// Return the summary-of-change of CR R1-2599685.

MATCH (cr:CR {tdocNumber: 'R1-2599685'}) WHERE cr.summaryOfChange IS NOT NULL RETURN cr.tdocNumber, cr.summaryOfChange

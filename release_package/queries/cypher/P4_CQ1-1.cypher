// P4_CQ1-1 — Phase 4 (CR rationale)
// Return the reason-for-change of CR R1-2504971.

MATCH (cr:CR {tdocNumber: 'R1-2504971'}) WHERE cr.reasonForChange IS NOT NULL RETURN cr.tdocNumber, cr.reasonForChange

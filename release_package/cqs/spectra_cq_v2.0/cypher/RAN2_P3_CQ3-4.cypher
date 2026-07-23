// SpectraCQ RAN2_P3_CQ3-4 (RAN2, phase 3) -- CQ3_CR
// Question: List the CRs that specify affected clauses (clause-tagged CRs).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10

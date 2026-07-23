// SpectraCQ RAN3_P3_CQ3-4 (RAN3, phase 3) -- CQ3_CR
// Question: List the CRs that record affected clauses (clause-level change survey).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN cr.tdocNumber, cr.clausesAffected, cr.crCategory ORDER BY cr.tdocNumber DESC LIMIT 10

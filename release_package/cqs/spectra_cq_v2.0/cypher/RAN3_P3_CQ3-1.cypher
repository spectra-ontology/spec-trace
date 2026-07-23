// SpectraCQ RAN3_P3_CQ3-1 (RAN3, phase 3) -- CQ3_CR
// Question: Return the spec and affected clauses modified by CR R3-253336 (change-scope lookup).
// Gold: 1 rows, primary column "sp.specNumber"

MATCH (cr:CR {tdocNumber: 'R3-253336'})-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, cr.clausesAffected

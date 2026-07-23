// SpectraCQ RAN3_P1_CQ2-5 (RAN3, phase 1) -- CQ2_Tdoc
// Question: Return the category and affected clauses of CR R3-258530 (impact assessment).
// Gold: 1 rows, primary column "c.tdocNumber"

MATCH (c:CR {tdocNumber: 'R3-258530'}) RETURN c.tdocNumber, c.crCategory, c.crNumber, c.clausesAffected

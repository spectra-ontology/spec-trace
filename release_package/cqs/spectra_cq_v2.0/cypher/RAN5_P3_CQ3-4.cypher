// SpectraCQ RAN5_P3_CQ3-4 (RAN5, phase 3) -- CQ3_CR
// Question: How many RAN5 CRs record the clauses they affect? (metadata completeness)
// Gold: 1 rows, primary column "crCount"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' AND cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' RETURN count(cr) AS crCount

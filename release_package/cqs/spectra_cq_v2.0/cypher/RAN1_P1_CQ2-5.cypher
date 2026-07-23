// SpectraCQ RAN1_P1_CQ2-5 (RAN1, phase 1) -- CQ2_Tdoc
// Question: What are the change category (F/A/B/C/D) and affected clauses of CR R1-2504971?
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R1-2504971'}) RETURN t.tdocNumber, t.title, t.crCategory, t.clausesAffected, t.status LIMIT 1

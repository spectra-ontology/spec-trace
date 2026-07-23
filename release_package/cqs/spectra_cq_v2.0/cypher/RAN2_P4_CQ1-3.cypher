// SpectraCQ RAN2_P4_CQ1-3 (RAN2, phase 4) -- CQ1
// Question: Return the consequences if CR R2-2508534 is not approved (adoption urgency).
// Gold: 1 rows, primary column "consequences"

MATCH (c:CR {tdocNumber: 'R2-2508534'}) RETURN c.consequencesIfNotApproved AS consequences LIMIT 1

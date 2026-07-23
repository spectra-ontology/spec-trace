// SpectraCQ RAN3_P4_CQ1-3 (RAN3, phase 4) -- CQ1
// Question: Return the consequences-if-not-approved of CR R3-237113 (adoption-urgency assessment).
// Gold: 1 rows, primary column "consequences"

MATCH (c:CR {tdocNumber: 'R3-237113'}) RETURN c.consequencesIfNotApproved AS consequences LIMIT 1

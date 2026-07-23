// SpectraCQ RAN4_P4_CQ1-3 (RAN4, phase 4) -- CQ1
// Question: Return the consequences-if-not-approved of CR R4-2107689 (impact-of-rejection review).
// Gold: 1 rows, primary column "consequences"

MATCH (c:CR {tdocNumber: 'R4-2107689'}) RETURN c.consequencesIfNotApproved AS consequences LIMIT 1

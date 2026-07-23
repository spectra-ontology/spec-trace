// SpectraCQ RAN5_P4_CQ1-3 (RAN5, phase 4) -- CQ1
// Question: What are the consequences if CR R5-261671 is not approved? (approval-impact assessment)
// Gold: 1 rows, primary column "consequences"

MATCH (c:CR {tdocNumber: 'R5-261671'}) RETURN c.consequencesIfNotApproved AS consequences LIMIT 1

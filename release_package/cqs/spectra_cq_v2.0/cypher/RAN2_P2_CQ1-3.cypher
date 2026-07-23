// SpectraCQ RAN2_P2_CQ1-3 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the working assumptions from meeting RAN2#115 (provisional-decision review).
// Gold: 11 rows, primary column "wa.resolutionId"

MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15

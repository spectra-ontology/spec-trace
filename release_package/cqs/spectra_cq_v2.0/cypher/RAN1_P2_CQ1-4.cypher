// SpectraCQ RAN1_P2_CQ1-4 (RAN1, phase 2) -- CQ1_Resolution
// Question: List the working assumptions from meeting RAN1#115 (items that may be revisited).
// Gold: 5 rows, primary column "wa.resolutionId"

MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15

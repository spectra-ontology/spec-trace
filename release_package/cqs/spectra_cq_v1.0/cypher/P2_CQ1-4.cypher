// SpectraCQ P2_CQ1-4 — CQ1_Resolution조회
// Question (English): List the Working Assumptions of meeting RAN1#115 (revisitable agenda items).
// Schema area: classes=['Meeting', 'WorkingAssumption'], rels=['MADE_AT']

MATCH (wa:WorkingAssumption)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'}) RETURN wa.resolutionId, wa.content ORDER BY wa.sequence LIMIT 15

// SpectraCQ P2_CQ5-6 — CQ5_기술트렌드
// Question (English): Return the Agreement count per meeting from RAN1#100 to RAN1#121 (standardization-activity trend).
// Schema area: classes=['Agreement', 'Meeting'], rels=['MADE_AT']

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumber IN ['RAN1#100', 'RAN1#101', 'RAN1#102', 'RAN1#103', 'RAN1#104', 'RAN1#105', 'RAN1#106', 'RAN1#107', 'RAN1#108', 'RAN1#109', 'RAN1#110', 'RAN1#111', 'RAN1#112', 'RAN1#113', 'RAN1#114', 'RAN1#115', 'RAN1#116', 'RAN1#117', 'RAN1#118', 'RAN1#119', 'RAN1#120', 'RAN1#121'] RETURN m.meetingNumber, count(a) AS agreementCount ORDER BY m.meetingNumber

// SpectraCQ P3_CQ022 — CR_TS_변경추적
// Question (English): Return per-meeting CR-submission trend for TS 38.213 (standardization-activity dynamics).
// Schema area: classes=['CR', 'Meeting', 'Spec'], rels=['MODIFIES', 'PRESENTED_AT']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) WITH m.meetingNumber AS meeting, m.meetingNumberInt AS meetingInt, count(cr) AS crCount RETURN meeting, crCount ORDER BY meetingInt

// SpectraCQ RAN1_P3_CQ022 (RAN1, phase 3) -- CR_TS
// Question: Show the trend of TS 38.213 CR submissions per meeting (standardization-activity trend).
// Gold: 47 rows, primary column "meeting"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) WITH m.meetingNumber AS meeting, m.meetingNumberInt AS meetingInt, count(cr) AS crCount RETURN meeting, crCount ORDER BY meetingInt

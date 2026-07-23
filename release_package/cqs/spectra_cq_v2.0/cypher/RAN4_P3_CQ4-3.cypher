// SpectraCQ RAN4_P3_CQ4-3 (RAN4, phase 3) -- CQ4_Resolution
// Question: How many CRs presented at RAN4#111 modify spec 38.133? (meeting-scoped change count).
// Gold: 1 rows, primary column "crCount"

MATCH (m:Meeting {meetingNumber: 'RAN4#111'})<-[:PRESENTED_AT]-(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN count(cr) AS crCount

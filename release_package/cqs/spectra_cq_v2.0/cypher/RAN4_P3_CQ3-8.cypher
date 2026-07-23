// SpectraCQ RAN4_P3_CQ3-8 (RAN4, phase 3) -- CQ3_CR
// Question: How many Rel-18 CRs modify spec 38.133? (release-scoped change count).
// Gold: 1 rows, primary column "crCount"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:TARGET_RELEASE]->(r:Release {releaseName: 'Rel-18'}) RETURN count(cr) AS crCount

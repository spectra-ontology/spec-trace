// P2_CQ1-3 — Phase 2 (Resolution lookup)
// List the Conclusions recorded at meeting RAN1#121.

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence LIMIT 15

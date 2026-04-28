// SpectraCQ P2_CQ1-3 — CQ1_Resolution조회
// Question (English): List the Conclusions recorded at the most recent meeting (RAN1#121) for open-issue review.
// Schema area: classes=['Conclusion', 'Meeting'], rels=['MADE_AT']

MATCH (c:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) RETURN c.resolutionId, c.content ORDER BY c.sequence LIMIT 15

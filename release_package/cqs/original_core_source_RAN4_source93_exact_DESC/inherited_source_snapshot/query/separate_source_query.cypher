MATCH (d:SourceMeetingDocument)
WHERE d.meetingNumberInt = 93
  AND d.sourceType IN ['CR','draftCR','pCR']
  AND d.finalDocumentaryStatus IN ['agreed','approved','endorsed']
WITH d ORDER BY d.tdocNumber ASC LIMIT 10
OPTIONAL MATCH (d)-[:SOURCE_HAS_OWN_SUMMARY]->(s:SourceOwnCRSummary)
RETURN s.sourceSummary AS summary
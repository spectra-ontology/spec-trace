MATCH (d:SourceMeetingDocument)-[:SOURCE_HAS_OWN_SUMMARY]->(s:SourceOwnCRSummary)
WHERE d.meetingNumberInt = 93
  AND d.sourceType IN ['CR','draftCR','pCR']
  AND d.finalDocumentaryStatus IN ['agreed','approved','endorsed']
  AND s.sourceSummary IS NOT NULL
RETURN d.tdocNumber AS tdocNumber, s.sourceSummary AS summary
ORDER BY d.tdocNumber DESC LIMIT 10
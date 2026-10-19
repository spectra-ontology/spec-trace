SELECT d.tdocNumber AS tdocNumber, s.sourceSummary AS summary
FROM SourceMeetingDocument AS d
JOIN rel_SOURCE_HAS_OWN_SUMMARY AS r ON r.src_id=d.node_id
JOIN SourceOwnCRSummary AS s ON s.node_id=r.dst_id
WHERE d.meetingNumberInt=93 AND d.sourceType IN ('CR','draftCR','pCR')
AND d.finalDocumentaryStatus IN ('agreed','approved','endorsed')
AND s.sourceSummary IS NOT NULL
ORDER BY d.tdocNumber DESC LIMIT 10
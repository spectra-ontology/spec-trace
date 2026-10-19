WITH selected AS (
 SELECT node_id, tdocNumber
 FROM SourceMeetingDocument
 WHERE meetingNumberInt=93 AND sourceType IN ('CR','draftCR','pCR')
   AND finalDocumentaryStatus IN ('agreed','approved','endorsed')
 ORDER BY tdocNumber ASC
 LIMIT 10
)
SELECT s.sourceSummary AS summary
FROM selected d
LEFT JOIN rel_SOURCE_HAS_OWN_SUMMARY h ON h.src_id=d.node_id
LEFT JOIN SourceOwnCRSummary s ON s.node_id=h.dst_id
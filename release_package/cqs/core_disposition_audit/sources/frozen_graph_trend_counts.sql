
SELECT m.node_id, m.canonicalMeetingNumber, m.meetingNumberInt,
 COUNT(DISTINCT r.node_id) AS all_resolution_count,
 COUNT(DISTINCT CASE WHEN EXISTS(
   SELECT 1 FROM rel_REFERENCES x JOIN Tdoc t ON t.node_id=x.dst_id
   WHERE x.src_id=r.node_id) THEN r.node_id END) AS linked_resolution_count,
 COUNT(DISTINCT CASE WHEN EXISTS(
   SELECT 1 FROM rel_REFERENCES x
   JOIN Tdoc t ON t.node_id=x.dst_id
   JOIN rel_SUBMITTED_BY s ON s.src_id=t.node_id
   JOIN Company c ON c.node_id=s.dst_id
   WHERE x.src_id=r.node_id AND c.companyName=:company) THEN r.node_id END) AS company_resolution_count
FROM Meeting m JOIN rel_MADE_AT ma ON ma.dst_id=m.node_id
JOIN Resolution r ON r.node_id=ma.src_id
GROUP BY m.node_id, m.canonicalMeetingNumber, m.meetingNumberInt
ORDER BY m.meetingNumberInt, m.canonicalMeetingNumber, m.node_id
;

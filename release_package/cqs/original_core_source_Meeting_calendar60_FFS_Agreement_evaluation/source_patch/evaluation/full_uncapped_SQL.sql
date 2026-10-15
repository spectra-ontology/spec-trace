WITH event_period AS (
      SELECT a.node_id AS agreement_node_id, max(m.sourceReportedEndDate) AS meetingPeriodEndDate
      FROM Agreement a JOIN rel_MADE_AT made ON made.src_id=a.node_id
      JOIN Meeting m ON m.node_id=made.dst_id
      GROUP BY a.node_id
    )
    SELECT DISTINCT a.resolutionId AS resolutionId,a.content AS content,p.meetingPeriodEndDate,
                    i.agendaNumber AS agendaNumber,a.sequence AS sequence
    FROM Agreement a JOIN event_period p ON p.agreement_node_id=a.node_id
    LEFT JOIN rel_RESOLUTION_BELONGS_TO own ON own.src_id=a.node_id
    LEFT JOIN AgendaItem i ON i.node_id=own.dst_id
    WHERE a.hasFFS=1
    ORDER BY p.meetingPeriodEndDate DESC,i.agendaNumber ASC NULLS LAST,a.sequence ASC NULLS LAST,a.resolutionId ASC

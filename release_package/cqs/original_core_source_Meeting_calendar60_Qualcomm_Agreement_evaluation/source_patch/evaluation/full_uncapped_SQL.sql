WITH company_documents AS (
      SELECT DISTINCT sb.src_id AS document_id
      FROM Company c JOIN rel_SUBMITTED_BY sb ON sb.dst_id=c.node_id
      JOIN Tdoc t ON t.node_id=sb.src_id WHERE c.companyName='Qualcomm'
    ), company_agreements AS (
      SELECT DISTINCT a.node_id AS agreement_id
      FROM Agreement a JOIN rel_REFERENCES ref ON ref.src_id=a.node_id
      JOIN company_documents doc ON doc.document_id=ref.dst_id
    )
    SELECT a.resolutionId AS resolutionId,a.content AS content,
           max(m.sourceReportedEndDate) AS meetingPeriodEndDate
    FROM company_agreements q JOIN Agreement a ON a.node_id=q.agreement_id
    JOIN rel_MADE_AT made ON made.src_id=a.node_id
    JOIN Meeting m ON m.node_id=made.dst_id
    GROUP BY a.node_id,a.resolutionId,a.content
    ORDER BY meetingPeriodEndDate DESC,a.resolutionId ASC

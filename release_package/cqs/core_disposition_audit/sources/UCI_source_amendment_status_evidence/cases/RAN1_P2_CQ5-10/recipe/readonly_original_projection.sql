SELECT a.node_id,a.resolutionId,a.content,a.contentWithEquations,a.note,
    m.meetingNumber,m.meetingNumberInt FROM Agreement a JOIN edge e
    ON e.src_id=a.node_id AND e.rel_type='MADE_AT' JOIN Meeting m ON m.node_id=e.dst_id;

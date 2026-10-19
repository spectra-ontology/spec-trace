SELECT node_id,resolutionId,hasFFS,sequence FROM Agreement ORDER BY node_id;
SELECT m.node_id,m.meetingNumber,m.meetingNumberInt FROM rel_MADE_AT e JOIN Meeting m ON m.node_id=e.dst_id WHERE e.src_id=? ORDER BY m.node_id;
SELECT ag.node_id,ag.agendaNumber FROM rel_RESOLUTION_BELONGS_TO e JOIN AgendaItem ag ON ag.node_id=e.dst_id WHERE e.src_id=? ORDER BY ag.node_id;

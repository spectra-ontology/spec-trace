SELECT DISTINCT a.formalSourceContentWithTables AS content FROM Agreement a
                 JOIN rel_RESOLUTION_BELONGS_TO ra ON ra.src_id=a.node_id
                 JOIN AgendaItem ai ON ai.node_id=ra.dst_id
                 JOIN rel_MADE_AT am ON am.src_id=a.node_id
                 JOIN Meeting m ON m.node_id=am.dst_id
                 WHERE ai.agendaNumber='5.1' AND m.meetingNumber='RAN1#100'

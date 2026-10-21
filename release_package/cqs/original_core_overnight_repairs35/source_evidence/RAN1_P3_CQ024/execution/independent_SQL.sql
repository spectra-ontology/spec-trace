SELECT DISTINCT agr.resolutionId,COALESCE(agr.contentWithEquations,agr.content)AS content,m.meetingNumber,m.meetingNumberInt
 FROM Agreement agr JOIN rel_REFERENCES r ON r.src_id=agr.node_id JOIN CR cr ON cr.node_id=r.dst_id JOIN Tdoc t ON t.node_id=cr.node_id
 JOIN rel_MODIFIES x ON x.src_id=cr.node_id JOIN Spec sp ON sp.node_id=x.dst_id
 JOIN rel_MADE_AT ma ON ma.src_id=agr.node_id JOIN Meeting m ON m.node_id=ma.dst_id
 WHERE sp.specNumber='38.213' AND own_reference(agr.content,t.tdocNumber)=1
 ORDER BY m.meetingNumberInt DESC,m.meetingNumber DESC,agr.resolutionId

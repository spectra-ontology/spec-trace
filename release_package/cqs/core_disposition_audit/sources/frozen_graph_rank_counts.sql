SELECT co.companyName,
       count(DISTINCT t.node_id) AS distinctTdocs,
       count(DISTINCT r.node_id) AS distinctResolutions
FROM Resolution r
JOIN rel_REFERENCES rr ON rr.src_id=r.node_id
JOIN Tdoc t ON t.node_id=rr.dst_id
JOIN rel_MODIFIES m ON m.src_id=t.node_id
JOIN Spec s ON s.node_id=m.dst_id AND s.specNumber=?
JOIN rel_SUBMITTED_BY sb ON sb.src_id=t.node_id
JOIN Company co ON co.node_id=sb.dst_id
GROUP BY co.companyName
ORDER BY co.companyName;

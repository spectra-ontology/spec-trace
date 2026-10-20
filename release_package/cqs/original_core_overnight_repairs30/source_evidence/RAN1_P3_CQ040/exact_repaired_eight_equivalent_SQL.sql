WITH domain AS (
SELECT DISTINCT specNumber AS ts FROM Spec WHERE specNumber IN ('38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291')
), cr_members AS (
SELECT DISTINCT s.specNumber AS ts,c.node_id AS crId FROM CR c JOIN edge m ON m.src_id=c.node_id AND m.rel_type='MODIFIES' JOIN Spec s ON s.node_id=m.dst_id
), agr_members AS (
SELECT DISTINCT s.specNumber AS ts,a.node_id AS agrId FROM Agreement a JOIN edge r ON r.src_id=a.node_id AND r.rel_type='REFERENCES' JOIN CR c ON c.node_id=r.dst_id JOIN edge m ON m.src_id=c.node_id AND m.rel_type='MODIFIES' JOIN Spec s ON s.node_id=m.dst_id
), cr_counts AS (SELECT ts,count(*) AS crCnt FROM cr_members GROUP BY ts), agr_counts AS (SELECT ts,count(*) AS agrCnt FROM agr_members GROUP BY ts)
SELECT domain.ts,COALESCE(cr_counts.crCnt,0) AS crCnt,COALESCE(agr_counts.agrCnt,0) AS agrCnt FROM domain LEFT JOIN cr_counts ON cr_counts.ts=domain.ts LEFT JOIN agr_counts ON agr_counts.ts=domain.ts ORDER BY crCnt DESC,domain.ts ASC

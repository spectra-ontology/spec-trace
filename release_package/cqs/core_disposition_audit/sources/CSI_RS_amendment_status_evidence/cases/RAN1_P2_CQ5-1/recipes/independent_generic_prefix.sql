
WITH RECURSIVE
positive AS (
 SELECT a.node_id,a.resolutionId,a.content,a.contentWithEquations,a.note,
        m.meetingNumber,m.meetingNumberInt,e.edge_id
 FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type='MADE_AT'
 JOIN Meeting m ON m.node_id=e.dst_id WHERE instr(a.content,'CSI-RS')>0
),
lines(node_id,edge_id,offset0,line,tail) AS (
 SELECT node_id,edge_id,0,
 CASE WHEN instr(content,char(10))>0 THEN substr(content,1,instr(content,char(10))-1) ELSE content END,
 CASE WHEN instr(content,char(10))>0 THEN substr(content,instr(content,char(10))+1) ELSE NULL END
 FROM positive
 UNION ALL
 SELECT node_id,edge_id,offset0+length(line)+1,
 CASE WHEN instr(tail,char(10))>0 THEN substr(tail,1,instr(tail,char(10))-1) ELSE tail END,
 CASE WHEN instr(tail,char(10))>0 THEN substr(tail,instr(tail,char(10))+1) ELSE NULL END
 FROM lines WHERE tail IS NOT NULL
),
trimmed AS (
 SELECT node_id,edge_id,offset0,trim(line,char(9)||char(13)||char(11)||char(12)||' ') AS line FROM lines
),
tokens AS (
 SELECT *,instr(line,char(9)) AS tab1 FROM trimmed
),
parts AS (
 SELECT *,substr(line,1,tab1-1) AS tid,
 instr(substr(line,tab1+1),char(9)) AS tab2_relative FROM tokens
),
boundaries AS (
 SELECT node_id,edge_id,min(offset0) AS stop FROM parts
 WHERE tab1>0 AND substr(tid,1,3)='R1-' AND length(tid) BETWEEN 9 AND 11
 AND substr(tid,4) NOT GLOB '*[^0-9]*' AND tab2_relative>1
 AND length(line)>tab1+tab2_relative
 GROUP BY node_id,edge_id
)
SELECT p.*,CASE WHEN b.stop IS NULL THEN content
 WHEN b.stop=0 THEN '' ELSE substr(content,1,b.stop-1) END AS own_prefix
FROM positive p LEFT JOIN boundaries b ON b.node_id=p.node_id AND b.edge_id=p.edge_id
ORDER BY meetingNumberInt,resolutionId,edge_id

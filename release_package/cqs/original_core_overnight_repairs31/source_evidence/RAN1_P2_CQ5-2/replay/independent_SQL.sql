WITH RECURSIVE candidates AS (
SELECT a.node_id,a.resolutionId,a.content,m.meetingNumber,m.meetingNumberInt
FROM Agreement a JOIN edge r ON r.src_id=a.node_id AND r.rel_type='MADE_AT'
JOIN Meeting m ON m.node_id=r.dst_id
WHERE instr(a.content,'HARQ')>0 AND instr(a.content,'feedback')>0
), lines(node_id,ord,line,rest) AS (
SELECT node_id,-1,'',content||char(10) FROM Agreement
WHERE instr(content,'HARQ')>0 AND instr(content,'feedback')>0
UNION ALL SELECT node_id,ord+1,substr(rest,1,instr(rest,char(10))-1),substr(rest,instr(rest,char(10))+1)
FROM lines WHERE rest<>''
), headers AS (
SELECT node_id,min(ord) AS headerAt FROM lines
WHERE substr(trim(line),1,3)='R1-'
AND instr(trim(line),char(9)) BETWEEN 10 AND 12
AND substr(trim(line),4,instr(trim(line),char(9))-4) NOT GLOB '*[^0-9]*'
AND instr(substr(trim(line),instr(trim(line),char(9))+1),char(9))>1
AND length(substr(trim(line),instr(trim(line),char(9))+1))>
instr(substr(trim(line),instr(trim(line),char(9))+1),char(9))
GROUP BY node_id
), eligible AS (
SELECT l.node_id FROM lines l LEFT JOIN headers h ON h.node_id=l.node_id
WHERE l.ord>=0 AND (h.headerAt IS NULL OR l.ord<h.headerAt)
GROUP BY l.node_id HAVING max(instr(l.line,'HARQ')>0)=1 AND max(instr(l.line,'feedback')>0)=1
)
SELECT c.* FROM candidates c JOIN eligible e ON e.node_id=c.node_id
ORDER BY c.meetingNumberInt DESC,c.resolutionId;

WITH RECURSIVE lines(ag_id,seq,line,rest) AS (
 SELECT node_id,-1,'',coalesce(content,'')||char(10) FROM Agreement
 UNION ALL
 SELECT ag_id,seq+1,substr(rest,1,instr(rest,char(10))-1),substr(rest,instr(rest,char(10))+1)
 FROM lines WHERE rest<>''
), stops AS (
 SELECT ag_id,min(seq) AS stop FROM lines
 WHERE regexp('(?i)^\s*(?:Decision\s*:|R3-[0-9]{6}[\t ]+\S)',line) GROUP BY ag_id
)
SELECT DISTINCT c.node_id,c.tdocNumber,c.reasonForChange AS reason,c.summaryOfChange AS summary
FROM CR c JOIN rel_REFERENCES r ON r.dst_id=c.node_id
JOIN Agreement a ON a.node_id=r.src_id JOIN lines l ON l.ag_id=a.node_id
LEFT JOIN stops s ON s.ag_id=a.node_id
WHERE c.reasonForChange IS NOT NULL AND(s.stop IS NULL OR l.seq<s.stop)
AND(regexp('(?i)\b(?:agree|approve|endorse|adopt)\s+(?:(?!\b(?:CRs?|and|or|but|to|if|unless|until)\b|R3-[0-9]{6})[^,.;:!?\n])*?\bCRs?\b\s*(?:in\s*)?\(?(?:R3-[0-9]{6}\s*(?:,|and|or)\s*)*'||c.tdocNumber||'\b',l.line)
 OR regexp('(?i)\b'||c.tdocNumber||'\b(?:\s*(?:,|and)\s*R3-[0-9]{6}\b)*(?:\s*\([^.;:!?\n]*\))?\s*(?:(?:is|are|was|were)\s+)?(?:agreed|approved|endorsed|adopted)\b',l.line))
AND NOT regexp('(?i)\b(?:revision\s+of|replaces?|was|revised\s+from)\s+'||c.tdocNumber||'\b|\b'||c.tdocNumber||'\s+(?:rev\s+in|revised\s+to)\b',l.line)
AND NOT regexp('(?i)\b(?:not|never)\b[^.;]*\b(?:agree|agreed|approve|approved|endorse|endorsed|adopt|adopted)\b|^\s*no\s+CRs?\b',l.line)
AND NOT regexp('(?i)^\s*(?:if|unless|until)\b',l.line)
ORDER BY c.tdocNumber
WITH dref(ref, did) AS (
  SELECT id, id FROM document
  UNION
  SELECT number, id FROM document WHERE number IS NOT NULL
),
inpack(did, pid) AS (
  SELECT r.did, l.pack_id FROM cr_in_pack l JOIN dref r ON r.ref = l.cr
  UNION
  SELECT r.did, l.pack_id FROM pack_member l JOIN dref r ON r.ref = l.cr
),
mods(did, sid) AS (
  SELECT r.did, l.section_id FROM cr_modifies_section l JOIN dref r ON r.ref = l.cr
  UNION
  SELECT r.did, l.section_id FROM section_modified_by l JOIN dref r ON r.ref = l.cr
),
vdisp(did, code, wg_meeting) AS (
  SELECT r.did, d.code, COALESCE(m.label, m.id)
  FROM disposition d
  JOIN dref r ON r.ref = d.target
  JOIN resolution res ON res.id = d.resolution_id
  JOIN meeting m ON m.id = res.meeting_id
  WHERE replace(replace(replace(lower(trim(d.evidence_status)),'_',''),'-',''),' ','') = 'sourceverified' AND replace(replace(replace(lower(trim(d.scope)),'_',''),'-',''),' ','') IN ('wholedocument','document','whole','doc','wholedoc','fulldocument','entiredocument','entire','full') AND (replace(replace(replace(upper(trim(m.wg)),' ',''),'_',''),'-','') IN ('RAN5','R5','RANWG5','WG5','TSGRANWG5','TSGR5') OR (m.wg IS NULL AND (replace(replace(replace(upper(trim(m.label)),' ',''),'_',''),'-','') LIKE 'RAN5%' OR replace(replace(replace(upper(trim(m.label)),' ',''),'_',''),'-','') LIKE 'R5%' OR replace(replace(replace(upper(trim(m.label)),' ',''),'_',''),'-','') LIKE 'TSGR5%')))
),
tp(pid, tnum) AS (
  SELECT id, tsg_number FROM cr_pack WHERE pack_number = '{ANCHOR}' OR id = '{ANCHOR}'
),
base(did, dnum, spec, clause, rel, tnum) AS (
  SELECT DISTINCT doc.id, doc.number, s.spec, s.clause, replace(replace(replace(replace(replace(lower(trim(s.release)),'release',''),'rel',''),'-',''),' ',''),'_',''), tp.tnum
  FROM tp
  JOIN inpack ip ON ip.pid = tp.pid
  JOIN document doc ON doc.id = ip.did
  JOIN mods mo ON mo.did = doc.id
  JOIN section s ON s.id = mo.sid
  WHERE replace(replace(replace(replace(replace(lower(trim(s.release)),'release',''),'rel',''),'-',''),' ',''),'_','') = replace(replace(replace(replace(replace(lower(trim(doc.target_release)),'release',''),'rel',''),'-',''),' ',''),'_','')
    AND EXISTS (SELECT 1 FROM vdisp v WHERE v.did = doc.id)
),
bsec(spec, clause, rel, tnum) AS (
  SELECT DISTINCT spec, clause, rel, tnum FROM base
),
hist(spec, clause, rel, btnum, pack_number, tsg_meeting, tsg_number) AS (
  SELECT DISTINCT bs.spec, bs.clause, bs.rel, bs.tnum, p2.pack_number, p2.tsg_meeting, p2.tsg_number
  FROM bsec bs
  JOIN section s2 ON s2.spec = bs.spec AND s2.clause = bs.clause
  JOIN mods mo2 ON mo2.sid = s2.id
  JOIN document d2 ON d2.id = mo2.did
  JOIN inpack ip2 ON ip2.did = d2.id
  JOIN cr_pack p2 ON p2.id = ip2.pid
  WHERE replace(replace(replace(replace(replace(lower(trim(s2.release)),'release',''),'rel',''),'-',''),' ',''),'_','') = bs.rel
    AND replace(replace(replace(replace(replace(lower(trim(d2.target_release)),'release',''),'rel',''),'-',''),' ',''),'_','') = bs.rel
    AND p2.tsg_number < bs.tnum
)
SELECT DISTINCT h.spec AS specification, h.clause AS clause, h.pack_number AS cr_pack, h.tsg_meeting AS tsg_meeting
FROM hist h
WHERE h.tsg_number = (
  SELECT MAX(h2.tsg_number) FROM hist h2
  WHERE h2.spec = h.spec AND h2.clause = h.clause AND h2.rel = h.rel AND h2.btnum = h.btnum
)

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
x(did) AS (
  SELECT id FROM document WHERE number = '{ANCHOR}' OR id = '{ANCHOR}'
),
xs(spec, clause, rel) AS (
  SELECT DISTINCT s.spec, s.clause, replace(replace(replace(replace(replace(lower(trim(s.release)),'release',''),'rel',''),'-',''),' ',''),'_','')
  FROM x
  JOIN mods mo ON mo.did = x.did
  JOIN section s ON s.id = mo.sid
  WHERE replace(replace(replace(replace(replace(lower(trim(s.release)),'release',''),'rel',''),'-',''),' ',''),'_','') = replace(replace(replace(replace(replace(lower(trim('Rel-18')),'release',''),'rel',''),'-',''),' ',''),'_','')
)
SELECT DISTINCT xs.clause AS clause, d2.number AS document, v.code AS disposition,
       v.wg_meeting AS wg_meeting, p.pack_number AS cr_pack
FROM xs
JOIN section s2 ON s2.spec = xs.spec AND s2.clause = xs.clause
JOIN mods mo2 ON mo2.sid = s2.id
JOIN document d2 ON d2.id = mo2.did
JOIN vdisp v ON v.did = d2.id
JOIN inpack ip ON ip.did = d2.id
JOIN cr_pack p ON p.id = ip.pid
WHERE replace(replace(replace(replace(replace(lower(trim(s2.release)),'release',''),'rel',''),'-',''),' ',''),'_','') = xs.rel
  AND replace(replace(replace(replace(replace(lower(trim(d2.target_release)),'release',''),'rel',''),'-',''),' ',''),'_','') = xs.rel
  AND d2.id NOT IN (SELECT did FROM x)
  AND COALESCE(d2.number, '') <> '{ANCHOR}'

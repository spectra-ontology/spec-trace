WITH
docref AS (
  SELECT id AS ref, id AS doc_id FROM document
  UNION
  SELECT number, id FROM document WHERE number IS NOT NULL
),
packref AS (
  SELECT id AS ref, id AS pack_key FROM cr_pack
  UNION
  SELECT pack_number, id FROM cr_pack WHERE pack_number IS NOT NULL
),
memb AS (
  SELECT DISTINCT dr.doc_id AS doc_id, pr.pack_key AS pack_key
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) m
  JOIN docref dr ON dr.ref = m.cr
  JOIN packref pr ON pr.ref = m.pack_id
),
docr AS (
  SELECT id AS doc_id, COALESCE(number, id) AS doc_no, (CASE WHEN INSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(target_release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),'.')>0 THEN SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(target_release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),1,INSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(target_release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),'.')-1) ELSE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(target_release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ','') END) AS rel FROM document
),
cmod AS (
  SELECT DISTINCT d.doc_id AS doc_id, s.spec AS spec, s.clause AS clause, d.rel AS rel
  FROM (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by) x
  JOIN docref dr ON dr.ref = x.cr
  JOIN docr d ON d.doc_id = dr.doc_id
  JOIN section s ON s.id = x.section_id
  WHERE d.rel <> '' AND (CASE WHEN INSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(s.release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),'.')>0 THEN SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(s.release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),1,INSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(s.release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ',''),'.')-1) ELSE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(s.release,''))),'RELEASE',''),'REL',''),'R',''),'-',''),'_',''),' ','') END) = d.rel
),
vdisp AS (
  SELECT DISTINCT dr.doc_id AS doc_id, di.code AS code, COALESCE(mt.label, mt.id) AS wg_meeting
  FROM disposition di
  JOIN docref dr ON dr.ref = di.target
  JOIN resolution rs ON rs.id = di.resolution_id
  JOIN meeting mt ON mt.id = rs.meeting_id
  WHERE REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(di.evidence_status,''))),'-',''),'_',''),' ','') IN ('sourceverified','verifiedsource','verifiedfromsource','verified')
    AND REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(di.scope,''))),'-',''),'_',''),' ','') IN ('wholedocument','document','whole','fulldocument','entiredocument','full','entire','doc','wholedoc','tdoc','all','wholetdoc','fulltdoc')
    AND (REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(mt.wg,''))),'-',''),'_',''),' ','') IN ('ran3','r3','ranwg3','wg3','tsgranwg3','tsgran3','ranw3')
         OR (mt.wg IS NULL AND (REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(mt.label,''))),'-',''),'_',''),' ','') LIKE 'ran3%' OR REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(mt.label,''))),'-',''),'_',''),' ','') LIKE 'r3%'
                                OR REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(mt.label,''))),'-',''),'_',''),' ','') LIKE 'ranwg3%')))
),
tp AS (
  SELECT id AS pack_key, tsg_number AS tn FROM cr_pack WHERE pack_number = '{ANCHOR}' OR id = '{ANCHOR}'
),
pc AS (
  SELECT DISTINCT c.doc_id AS doc_id, c.spec AS spec, c.clause AS clause, c.rel AS rel, tp.tn AS tn
  FROM tp
  JOIN memb mb ON mb.pack_key = tp.pack_key
  JOIN cmod c ON c.doc_id = mb.doc_id
  WHERE c.doc_id IN (SELECT doc_id FROM vdisp)
),
earlier AS (
  SELECT DISTINCT k.spec AS spec, k.clause AS clause, k.rel AS rel, k.tn AS tn,
         p.tsg_number AS tsg_number, COALESCE(p.pack_number, p.id) AS pack_number, p.tsg_meeting AS tsg_meeting
  FROM (SELECT DISTINCT spec, clause, rel, tn FROM pc) k
  JOIN cmod c ON c.spec = k.spec AND c.clause = k.clause AND c.rel = k.rel
  JOIN memb mb ON mb.doc_id = c.doc_id
  JOIN cr_pack p ON p.id = mb.pack_key
  WHERE p.tsg_number < k.tn
)
SELECT DISTINCT d.doc_no AS document, pc.spec AS specification, pc.clause AS clause
FROM pc
JOIN docr d ON d.doc_id = pc.doc_id
WHERE NOT EXISTS (
  SELECT 1 FROM earlier e
  WHERE e.spec = pc.spec AND e.clause = pc.clause AND e.rel = pc.rel AND e.tn = pc.tn
)

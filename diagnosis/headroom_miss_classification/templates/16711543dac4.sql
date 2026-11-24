WITH
docref AS (
  SELECT id AS ref, id AS doc_id FROM document WHERE id IS NOT NULL
  UNION
  SELECT number AS ref, id AS doc_id FROM document WHERE number IS NOT NULL
),
packref AS (
  SELECT id AS ref, id AS pack_id FROM cr_pack WHERE id IS NOT NULL
  UNION
  SELECT pack_number AS ref, id AS pack_id FROM cr_pack WHERE pack_number IS NOT NULL
),
inpack AS (
  SELECT DISTINCT dr.doc_id AS doc_id, pr.pack_id AS pack_id
  FROM (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member) e
  JOIN docref dr ON dr.ref = e.cr
  JOIN packref pr ON pr.ref = e.pack_id
),
modsec AS (
  SELECT DISTINCT dr.doc_id AS doc_id, e.section_id AS section_id
  FROM (SELECT cr, section_id FROM cr_modifies_section
        UNION SELECT cr, section_id FROM section_modified_by) e
  JOIN docref dr ON dr.ref = e.cr
),
mods AS (
  SELECT DISTINCT ms.doc_id AS doc_id, s.spec AS spec, s.clause AS clause,
         CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(s.release),'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER) AS rel
  FROM modsec ms
  JOIN document d ON d.id = ms.doc_id
  JOIN section s ON s.id = ms.section_id
  WHERE CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(s.release),'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER) = CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(d.target_release),'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER)
),
verified AS (
  SELECT DISTINCT dr.doc_id AS doc_id, dp.code AS code, m.label AS wg_meeting
  FROM disposition dp
  JOIN docref dr ON dr.ref = dp.target
  JOIN resolution r ON r.id = dp.resolution_id
  JOIN meeting m ON (m.id = r.meeting_id OR m.label = r.meeting_id)
  WHERE LOWER(REPLACE(REPLACE(REPLACE(TRIM(dp.evidence_status),' ',''),'_',''),'-','')) IN ('sourceverified','verifiedsource')
    AND LOWER(REPLACE(REPLACE(REPLACE(TRIM(dp.scope),' ',''),'_',''),'-','')) IN ('wholedocument','document','whole','fulldocument','entiredocument','doc','wholedoc','tdoc','wholetdoc','entiretdoc','fulltdoc')
    AND (UPPER(REPLACE(REPLACE(REPLACE(TRIM(m.wg),' ',''),'_',''),'-','')) IN ('RAN3','R3','RANWG3','TSGRANWG3','WG3','3','RAN3WG') OR (m.wg IS NULL AND (m.label LIKE 'R3%' OR m.label LIKE '%RAN3%' OR m.label LIKE '%RAN_WG3%')))
),
target_pack AS (
  SELECT id AS pack_id, tsg_number AS p_num FROM cr_pack
  WHERE pack_number = '{ANCHOR}' OR id = '{ANCHOR}'
),
seeds AS (
  SELECT DISTINCT tp.p_num AS p_num, m.doc_id AS doc_id, m.spec AS spec,
         m.clause AS clause, m.rel AS rel
  FROM target_pack tp
  JOIN inpack ip ON ip.pack_id = tp.pack_id
  JOIN mods m ON m.doc_id = ip.doc_id
  WHERE m.rel IN (19)
    AND m.doc_id IN (SELECT doc_id FROM verified)
),
cand AS (
  SELECT DISTINCT s.p_num AS p_num, s.spec AS spec, s.clause AS clause, s.rel AS rel,
         cp2.pack_number AS pack_number, cp2.tsg_meeting AS tsg_meeting,
         cp2.tsg_number AS tsg_number
  FROM seeds s
  JOIN mods m2 ON m2.spec = s.spec AND m2.clause = s.clause AND m2.rel = s.rel
  JOIN inpack ip2 ON ip2.doc_id = m2.doc_id
  JOIN cr_pack cp2 ON cp2.id = ip2.pack_id
  WHERE cp2.tsg_number < s.p_num
)
SELECT DISTINCT c.spec AS specification, c.clause AS clause, c.pack_number AS cr_pack,
       c.tsg_meeting AS tsg_meeting
FROM cand c
WHERE c.tsg_number = (
  SELECT MAX(c2.tsg_number) FROM cand c2
  WHERE c2.p_num = c.p_num AND c2.spec = c.spec AND c2.clause = c.clause
    AND c2.rel = c.rel
)

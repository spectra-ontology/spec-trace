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
xdocs AS (
  SELECT id AS doc_id FROM document WHERE number = '{ANCHOR}' OR id = '{ANCHOR}'
),
xclauses AS (
  SELECT DISTINCT s.spec AS spec, s.clause AS clause, CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(s.release),'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER) AS rel
  FROM modsec ms
  JOIN section s ON s.id = ms.section_id
  WHERE ms.doc_id IN (SELECT doc_id FROM xdocs)
    AND CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(LOWER(s.release),'release',''),'rel',''),'r',''),'-',''),'_','')) AS INTEGER) = 18
)
SELECT DISTINCT x.clause AS clause, COALESCE(o.number, o.id) AS document,
       v.code AS disposition, v.wg_meeting AS wg_meeting, cp.pack_number AS cr_pack
FROM xclauses x
JOIN mods m ON m.spec = x.spec AND m.clause = x.clause AND m.rel = x.rel
JOIN document o ON o.id = m.doc_id
JOIN verified v ON v.doc_id = o.id
JOIN inpack ip ON ip.doc_id = o.id
JOIN cr_pack cp ON cp.id = ip.pack_id
WHERE o.id NOT IN (SELECT doc_id FROM xdocs)
  AND COALESCE(o.number, '') <> '{ANCHOR}'

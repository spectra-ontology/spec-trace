WITH docs AS (SELECT id, COALESCE(number, id) AS num, (CASE WHEN instr(replace(replace(replace(replace(replace(replace(lower(trim(target_release)),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),'.')>0 THEN substr(replace(replace(replace(replace(replace(replace(lower(trim(target_release)),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),1,instr(replace(replace(replace(replace(replace(replace(lower(trim(target_release)),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),'.')-1) ELSE replace(replace(replace(replace(replace(replace(lower(trim(target_release)),'release',''),'rel',''),'r',''),'-',''),' ',''),'_','') END) AS rel FROM document),
docmap AS (SELECT id AS doc_id, id AS k FROM document UNION SELECT id AS doc_id, number AS k FROM document WHERE number IS NOT NULL),
packmap AS (SELECT id AS pack_id, id AS k FROM cr_pack UNION SELECT id AS pack_id, pack_number AS k FROM cr_pack WHERE pack_number IS NOT NULL),
meetmap AS (SELECT id AS k, COALESCE(label, id) AS label, wg FROM meeting UNION SELECT label AS k, COALESCE(label, id) AS label, wg FROM meeting WHERE label IS NOT NULL),
sec AS (SELECT id, spec, clause, (CASE WHEN instr(replace(replace(replace(replace(replace(replace(lower(trim("release")),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),'.')>0 THEN substr(replace(replace(replace(replace(replace(replace(lower(trim("release")),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),1,instr(replace(replace(replace(replace(replace(replace(lower(trim("release")),'release',''),'rel',''),'r',''),'-',''),' ',''),'_',''),'.')-1) ELSE replace(replace(replace(replace(replace(replace(lower(trim("release")),'release',''),'rel',''),'r',''),'-',''),' ',''),'_','') END) AS rel FROM section),
modraw AS (SELECT cr, section_id FROM cr_modifies_section UNION SELECT cr, section_id FROM section_modified_by),
mods AS (SELECT DISTINCT dm.doc_id AS doc_id, mr.section_id AS section_id FROM modraw mr JOIN docmap dm ON dm.k = mr.cr),
packraw AS (SELECT cr, pack_id FROM cr_in_pack UNION SELECT cr, pack_id FROM pack_member),
inpack AS (SELECT DISTINCT dm.doc_id AS doc_id, pm.pack_id AS pack_id FROM packraw pr JOIN docmap dm ON dm.k = pr.cr JOIN packmap pm ON pm.k = pr.pack_id),
okdisp AS (SELECT DISTINCT dm.doc_id AS doc_id, dp.code AS code, mm.label AS wg_meeting FROM disposition dp JOIN docmap dm ON dm.k = dp.target JOIN resolution r ON r.id = dp.resolution_id JOIN meetmap mm ON mm.k = r.meeting_id WHERE lower(replace(replace(replace(trim(dp.evidence_status),'_',''),' ',''),'-','')) IN ('sourceverified','verifiedsource') AND lower(replace(replace(replace(trim(dp.scope),'_',''),' ',''),'-','')) IN ('wholedocument','document','whole','fulldocument','entiredocument','doc','wholedoc','tdoc','wholetdoc','full') AND (upper(replace(replace(replace(trim(COALESCE(mm.wg,'')),' ',''),'_',''),'-','')) IN ('RAN2','R2','RANWG2','TSGRANWG2','WG2','TSGR2','RWG2') OR upper(replace(replace(replace(trim(COALESCE(mm.wg,'')),' ',''),'_',''),'-','')) LIKE 'RAN2%')),
anchor AS (SELECT id FROM document WHERE number = '{ANCHOR}' OR id = '{ANCHOR}'),
acl AS (SELECT DISTINCT s.spec, s.rel, s.clause FROM anchor a JOIN mods mo ON mo.doc_id = a.id JOIN sec s ON s.id = mo.section_id WHERE s.rel = '16')
SELECT DISTINCT s2.clause AS clause, d.num AS document, od.code AS disposition, od.wg_meeting AS wg_meeting, COALESCE(cp.pack_number, cp.id) AS cr_pack
FROM acl JOIN sec s2 ON s2.spec = acl.spec AND s2.rel = acl.rel AND s2.clause = acl.clause
JOIN mods mo ON mo.section_id = s2.id
JOIN docs d ON d.id = mo.doc_id
JOIN okdisp od ON od.doc_id = d.id
JOIN inpack ip ON ip.doc_id = d.id
JOIN cr_pack cp ON cp.id = ip.pack_id
WHERE d.rel = '16' AND d.id NOT IN (SELECT id FROM anchor)

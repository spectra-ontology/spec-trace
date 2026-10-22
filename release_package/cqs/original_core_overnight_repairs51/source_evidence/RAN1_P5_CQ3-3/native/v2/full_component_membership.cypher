// Prospective original-question repair; no source IDs, labels, source-body runtime input.
MATCH (known:WorkItem)
WITH collect(DISTINCT known.workItemCode) AS knownCodes
MATCH (tr:TechnicalReport {trNumber: '38.824'})-[:RELATED_TO_WORK_ITEM]->(study:WorkItem)
WHERE left(study.workItemCode, 3) = 'FS_'
WITH knownCodes, tr, substring(study.workItemCode, 3) + '-Core' AS familyCode
MATCH (family:WorkItem {workItemCode: familyCode})<-[:RELATED_TO]-(cr:CR)-[:MODIFIES]->(target:Spec)
WHERE target.specNumber IN ['38.211', '38.214'] AND cr.status = 'agreed'
MATCH (cr)-[:RELATED_TO]->(other:WorkItem)
WITH knownCodes, tr, family, cr, target.specNumber AS specNumber,
     collect(DISTINCT other.workItemCode) AS carrierCodes
UNWIND ['reasonForChange', 'summaryOfChange'] AS field
WITH knownCodes, tr, family, cr, specNumber, carrierCodes, field,
     trim(coalesce(cr[field], '')) AS raw
WITH knownCodes, tr, family, cr, specNumber, carrierCodes, field, raw,
     [p IN split(replace(replace(replace(replace(raw,
       '\nIn section', '\n\nIn section'), '\nIn clause', '\n\nIn clause'),
       '\nIn Section', '\n\nIn Section'), '\nIn Clause', '\n\nIn Clause'), '\n\n')
       WHERE trim(p) <> '' | trim(p)] AS chunks
WITH knownCodes, tr, family, cr, specNumber, carrierCodes, field, raw, chunks,
     toLower(last(split(replace(family.workItemCode, '-Core', ''), '_'))) AS topic
WITH tr, family, cr, specNumber, carrierCodes, field,
     CASE WHEN size(carrierCodes) = 1
       THEN CASE WHEN raw = '' THEN [] ELSE [raw] END
       ELSE reduce(state = {active: false, selected: []}, p IN chunks |
         CASE WHEN size([t IN split(replace(p, '\n', ','), ',') WHERE trim(t) <> '']) > 0
           AND all(t IN [t IN split(replace(p, '\n', ','), ',') WHERE trim(t) <> '' | trim(t)] WHERE t IN knownCodes)
         THEN {active: family.workItemCode IN [t IN split(replace(p, '\n', ','), ',') WHERE trim(t) <> '' | trim(t)], selected: state.selected}
         WHEN state.active OR toLower(p) CONTAINS topic
         THEN {active: state.active, selected: state.selected + [p]}
         ELSE state END).selected END AS pieces
WHERE size(pieces) > 0
OPTIONAL MATCH (cr)-[:MODIFIES_SECTION]->(section:Section)
WITH tr, cr, specNumber, carrierCodes, field, pieces,
     CASE WHEN size(carrierCodes) = 1 OR
       any(p IN pieces WHERE p =~ ('(?s).*(^|[^0-9.])' + replace(section.sectionNumber, '.', '\\.') + '([^0-9.]|$).*'))
       THEN section.sectionNumber ELSE null END AS selectedSection
ORDER BY selectedSection
WITH tr, cr, specNumber, field, pieces,
     collect(DISTINCT selectedSection) AS sections
WITH tr, cr, specNumber, field, sections,
     reduce(description = '', p IN pieces |
       description + CASE WHEN description = '' THEN '' ELSE '\n\n' END +
       cr.tdocNumber + ' ' + field + ': ' + p) AS fieldDescription
RETURN specNumber, cr.id AS CRid, field, sections, pieces ORDER BY specNumber, CRid, field

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)
WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> ''
MATCH (cr)-[:MODIFIES]->(sp:Spec)
WITH r, cr, sp, split(coalesce(r.content, ''), '\n') AS lines
WITH r, cr, sp, lines,
  [i IN range(0, size(lines)-1) WHERE
    (i > 0 AND trim(lines[i]) =~ '(?i)Proposal\\s+[0-9]+([.\\s:\\[\\-].*)?') OR
    (trim(lines[i]) =~ 'R2-[0-9]{7}\\t.*' AND NOT (
      coalesce(last([p IN lines[0..i] WHERE trim(p) <> '']), '') =~ '(?i).*\\bCRs?\\s*' AND
      coalesce(head([p IN lines[i+1..] WHERE trim(p) <> '']), '') =~ '(?i)(can|are|is)\\b.*'))
  ] AS boundaries,
  [i IN range(0, size(lines)-1) WHERE trim(lines[i]) =~ 'R2-[0-9]{7}\\t.*'] AS headers
WITH r, cr, sp, lines, headers,
  lines[0..coalesce(head(boundaries), size(lines))] AS ownLines,
  head(headers) AS firstHeader
WITH r, cr, sp, lines, ownLines, firstHeader,
  CASE WHEN firstHeader IS NULL THEN [] ELSE split(trim(lines[firstHeader]), '\t') END AS firstCells,
  [token IN split(toLower(replace(replace(replace(replace(replace(
    reduce(s = '', p IN ownLines | s + ' ' + p), '(', ' '), ')', ' '), ',', ' '), '.', ' '), ':', ' ')), ' ')
    WHERE token =~ 'case-[0-9]+'] AS ownCaseTokens
WITH r, cr, sp, lines, ownLines, firstHeader, firstCells, ownCaseTokens,
  [i IN range(0, size(lines)-1) WHERE toLower(lines[i]) STARTS WITH 'scope:'
    AND any(token IN ownCaseTokens WHERE toLower(lines[i]) CONTAINS
      'taking the conclusion for ' + token + ' into account')] AS ownConclusionScopes
WHERE
  any(line IN ownLines WHERE line =~ '(?s).*(?<![A-Za-z0-9])' + cr.tdocNumber + '(?![0-9]).*')
  OR (firstHeader IS NOT NULL
      AND none(i IN range(1, firstHeader-1) WHERE trim(lines[i]) =~ '(?i)Proposal\\s+[0-9]+([.\\s:\\[\\-].*)?')
      AND size(firstCells) >= 4 AND toLower(firstCells[3]) IN ['cr', 'draftcr', 'pcr']
      AND cr.title = firstCells[1])
  OR coalesce(any(scope IN ownConclusionScopes WHERE cr.title =
      split(trim(lines[head([j IN range(scope+1, size(lines)-1)
        WHERE trim(lines[j]) =~ 'R2-[0-9]{7}\\t.*'
          AND size(split(trim(lines[j]), '\t')) >= 4
          AND toLower(split(trim(lines[j]), '\t')[3]) IN ['cr', 'draftcr', 'pcr']])]), '\t')[1]), false)
RETURN r.resolutionId, cr.tdocNumber, cr.clausesAffected, sp.specNumber
ORDER BY r.resolutionId, cr.tdocNumber, sp.specNumber
LIMIT 10
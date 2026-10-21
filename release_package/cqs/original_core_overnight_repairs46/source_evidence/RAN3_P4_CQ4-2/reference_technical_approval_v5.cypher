MATCH (a:Agreement)-[:REFERENCES]->(c:CR)
WHERE c.reasonForChange IS NOT NULL
WITH a, c, reduce(s = {open: true, lines: []}, line IN split(coalesce(a.content, ''), '\n') |
  CASE WHEN NOT s.open OR line =~ '(?i)^\\s*(?:Decision\\s*:|R3-[0-9]{6}[\\t ]+\\S).*'
    THEN {open: false, lines: s.lines}
    ELSE {open: true, lines: s.lines + [line]}
  END) AS technical
WHERE any(line IN technical.lines WHERE
  (line =~ ('(?i).*\\b(?:agree|approve|endorse|adopt)\\s+(?:(?!\\b(?:CRs?|and|or|but|to|if|unless|until)\\b|R3-[0-9]{6})[^,.;:!?\\n])*?\\bCRs?\\b\\s*(?:in\\s*)?\\(?(?:R3-[0-9]{6}\\s*(?:,|and|or)\\s*)*' + c.tdocNumber + '\\b.*')
   OR line =~ ('(?i).*\\b' + c.tdocNumber + '\\b(?:\\s*(?:,|and)\\s*R3-[0-9]{6}\\b)*(?:\\s*\\([^.;:!?\\n]*\\))?\\s*(?:(?:is|are|was|were)\\s+)?(?:agreed|approved|endorsed|adopted)\\b.*'))
  AND NOT line =~ ('(?i).*(?:\\b(?:revision\\s+of|replaces?|was|revised\\s+from)\\s+' + c.tdocNumber + '\\b|\\b' + c.tdocNumber + '\\s+(?:rev\\s+in|revised\\s+to)\\b).*')
  AND NOT line =~ '(?i).*(?:\\b(?:not|never)\\b[^.;]*\\b(?:agree|agreed|approve|approved|endorse|endorsed|adopt|adopted)\\b|^\\s*no\\s+CRs?\\b).*'
  AND NOT line =~ '(?i)^\\s*(?:if|unless|until)\\b.*')
WITH DISTINCT c ORDER BY c.tdocNumber LIMIT 5
RETURN c.tdocNumber AS tdocNumber, c.reasonForChange AS reason, c.summaryOfChange AS summary
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'})
WHERE (a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved'))
   OR (a.content =~ '(?is).*\\b(?:agree(?:d)?|approv(?:ed|e)|endors(?:ed|e)|adopt(?:ed)?|adapt(?:ed)?)\\b.*'
       AND a.content =~ '(?is).*\\b(?:TPs?|text\\s+proposals?)\\b.*'
       AND (a.content =~ '(?is).*\\bTS\\s*\\d{2}\\.\\d{3}\\b.*'
            OR a.content =~ '(?is).*\\b(?:TPs?|text\\s+proposals?)\\s+\\d+(?:\\.\\d+)*(?:-\\d+)?(?:\\s*\\([^)]*\\))?.*\\bsection\\s+\\d+(?:\\.\\d+)+.*\\bR1-\\d{7}\\b.*'))
RETURN a.resolutionId, a.content
ORDER BY a.sequence, a.resolutionId
// SpectraCQ RAN1_P3_CQ043 (RAN1, phase 3) -- 
// Question: Summarize the graph: node and relationship counts by type (overall graph scale).
// Gold: 8 rows, primary column "label"

CALL { MATCH (n:Section) RETURN 'Section' AS label, count(n) AS cnt UNION ALL MATCH (n:TSTable) RETURN 'TSTable' AS label, count(n) AS cnt UNION ALL MATCH (n:TSFigure) RETURN 'TSFigure' AS label, count(n) AS cnt UNION ALL MATCH (n:Spec) RETURN 'Spec' AS label, count(n) AS cnt UNION ALL MATCH (n:CR) RETURN 'CR' AS label, count(n) AS cnt UNION ALL MATCH (n:Meeting) RETURN 'Meeting' AS label, count(n) AS cnt UNION ALL MATCH (n:Company) RETURN 'Company' AS label, count(n) AS cnt UNION ALL MATCH (n:Resolution) RETURN 'Resolution' AS label, count(n) AS cnt } RETURN label, cnt ORDER BY cnt DESC

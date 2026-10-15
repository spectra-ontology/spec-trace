WITH section_owners AS (
 SELECT sec.node_id AS section_node, sp.specNumber AS family
 FROM Section sec JOIN edge own ON own.src_id=sec.node_id AND own.rel_type='BELONGS_TO_SPEC'
 JOIN Spec sp ON sp.node_id=own.dst_id
), section_counts AS (SELECT family,count(DISTINCT section_node) AS n FROM section_owners GROUP BY family),
 table_counts AS (SELECT so.family,count(DISTINCT tbl.node_id) AS n FROM section_owners so
 JOIN edge own ON own.dst_id=so.section_node AND own.rel_type='TABLE_IN_SECTION'
 JOIN TSTable tbl ON tbl.node_id=own.src_id GROUP BY so.family),
 figure_counts AS (SELECT so.family,count(DISTINCT fig.node_id) AS n FROM section_owners so
 JOIN edge own ON own.dst_id=so.section_node AND own.rel_type='FIGURE_IN_SECTION'
 JOIN TSFigure fig ON fig.node_id=own.src_id GROUP BY so.family)
 SELECT sc.family AS specNumber,sc.n AS sectionCount,coalesce(tc.n,0) AS tableCount,
 coalesce(fc.n,0) AS figureCount FROM section_counts sc
 LEFT JOIN table_counts tc ON tc.family=sc.family LEFT JOIN figure_counts fc ON fc.family=sc.family
 ORDER BY specNumber

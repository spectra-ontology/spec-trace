
SELECT sec.node_id,sec.sectionId,sec.sectionNumber,sec.sectionTitle,sec.level,
 sp.node_id AS spec_node_id,sp.specNumber,sp.specRelease,sp.specVersion,
 (SELECT COUNT(DISTINCT tbl.node_id) FROM rel_CONTAINS_TABLE e JOIN TSTable tbl
 ON tbl.node_id=e.dst_id WHERE e.src_id=sec.node_id) AS direct_distinct_tables,
 (SELECT COUNT(DISTINCT child.node_id) FROM rel_HAS_SUB_SECTION e JOIN Section child
 ON child.node_id=e.dst_id WHERE e.src_id=sec.node_id) AS direct_distinct_child_sections
FROM Section sec JOIN rel_BELONGS_TO_SPEC b ON b.src_id=sec.node_id
JOIN Spec sp ON sp.node_id=b.dst_id
ORDER BY sec.node_id,sp.node_id
;

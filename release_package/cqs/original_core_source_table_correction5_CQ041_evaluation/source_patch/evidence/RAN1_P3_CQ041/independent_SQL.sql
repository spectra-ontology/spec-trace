WITH direct_table_sets AS (
 SELECT sec.node_id AS section_node,sec.sectionId AS sectionId,tbl.node_id AS table_node
 FROM Section sec JOIN edge own ON own.src_id=sec.node_id AND own.rel_type='CONTAINS_TABLE'
 JOIN TSTable tbl ON tbl.node_id=own.dst_id GROUP BY sec.node_id,sec.sectionId,tbl.node_id)
 SELECT sectionId AS "sec.sectionId",count(*) AS tableCount FROM direct_table_sets
 GROUP BY section_node,sectionId HAVING count(*)>=5 ORDER BY sectionId

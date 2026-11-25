"""Inspect the explicit U003 documentary anchor; no engineering answer generation."""
import argparse, gzip, hashlib, json, sqlite3, time
from pathlib import Path

SQL = """SELECT DISTINCT d.number, d.doc_type, d.cr_number, d.spec,
 d.target_release, d.list_status, d.presented_at,
 x.code, r.meeting_id, x.evidence_path, x.evidence_sha256,
 p.pack_number, p.tsg_meeting, s.spec, s.release, s.clause
FROM document d
LEFT JOIN disposition x ON x.target=d.id
 AND x.evidence_status='source_verified' AND x.scope='whole_document'
LEFT JOIN resolution r ON r.id=x.resolution_id
LEFT JOIN (SELECT cr,pack_id FROM pack_member
 UNION SELECT cr,pack_id FROM cr_in_pack) pm ON pm.cr=d.id
LEFT JOIN cr_pack p ON p.id=pm.pack_id
LEFT JOIN (SELECT cr,section_id FROM cr_modifies_section
 UNION SELECT cr,section_id FROM section_modified_by) sl ON sl.cr=d.id
LEFT JOIN section s ON s.id=sl.section_id
WHERE d.number=? ORDER BY d.number,x.code,r.meeting_id,p.pack_number,s.spec,s.release,s.clause"""

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--release',type=Path,required=True)
    ap.add_argument('--database',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); release=a.release.resolve(); db=a.database.resolve()
    inputs=release/'studies/practitioner_questions/question_analysis.json'
    analysis=json.loads(inputs.read_text())
    units=[u for u in analysis['units'] if u['first_judgment']['type'] in ['mixed','process_trace']]
    assert [u['unit_id'] for u in units]==['U003','U004','U015','U021','U023']
    u=units[0];assert 'R5-253194' in u['question_paraphrase_en']
    packed=release/'sqlite/RAN5.sqlite.gz';unpacked=release/'sqlite/RAN5.sqlite'
    before=digest(db)
    if packed.exists():
        h=hashlib.sha256()
        with gzip.open(packed,'rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        assert h.hexdigest()==before
        public_input={'path':'sqlite/RAN5.sqlite.gz','sha256':digest(packed),'decompressed_sha256':before}
    else:
        assert digest(unpacked)==before
        public_input={'path':'sqlite/RAN5.sqlite','sha256':before}
    c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
    c.execute('PRAGMA query_only=ON');tick=time.monotonic()
    c.set_progress_handler(lambda: int(time.monotonic()-tick>60),10000)
    cursor=c.execute(SQL,('R5-253194',));fields=[d[0] for d in cursor.description];rows=cursor.fetchall();c.close()
    assert digest(db)==before
    result={'protocol_sha256':digest(Path(__file__).with_name('protocol.json')),
            'checker_sha256':digest(Path(__file__)),'question_analysis_sha256':digest(inputs),
            'units':units,'public_database':public_input,'database_before_after_unchanged':True,
            'runtime':{'sqlite':sqlite3.sqlite_version,'cap_seconds':60,'mode':'ro immutable query_only'},
            'lookup':{'unit_id':'U003','curated_anchor':'R5-253194','sql':SQL,'parameters':['R5-253194'],
                      'fields':fields,'rows':rows,'row_count':len(rows),'seconds':time.monotonic()-tick},
            'scope':'Curated documentary lookup for one explicit anchor; preserves classifier disagreement. All five units retained, with no new model judgments or whole-question success measurement.'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'unit':'U003','rows':len(rows),'fields':fields,'results':rows},ensure_ascii=False))

if __name__=='__main__':main()

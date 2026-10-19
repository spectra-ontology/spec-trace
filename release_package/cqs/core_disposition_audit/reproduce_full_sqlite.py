"""Optional full frozen-graph SQL check; requires separately restored SQLite files."""
import argparse
import json
from pathlib import Path
import sqlite3

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--db-dir',type=Path,required=True);a=p.parse_args()
    expected=json.loads((HERE/'expected.json').read_text())
    checks=[]
    for wg in ['RAN1','RAN3','RAN4']:
        db=(a.db_dir/(wg+'.sqlite')).resolve()
        c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
        if wg=='RAN1':
            rows=[dict(r) for r in c.execute((HERE/'sources/frozen_graph_area_operands.sql').read_text())]
            assert rows==expected['area_operand_counts'];checks.append({'wg':wg,'area_operand_rows_equal':len(rows)})
        else:
            spec,company=('38.423','ZTE') if wg=='RAN3' else ('38.133','Samsung')
            rank=[dict(r) for r in c.execute((HERE/'sources/frozen_graph_rank_counts.sql').read_text(),(spec,))]
            trend=[dict(r) for r in c.execute((HERE/'sources/frozen_graph_trend_counts.sql').read_text(),{'company':company})]
            assert rank==expected['ranks'][wg];assert trend==expected['trends'][wg]
            checks.append({'wg':wg,'rank_company_rows_equal':len(rank),'Resolution_bearing_meeting_rows_equal':len(trend)})
        c.close()
    print(json.dumps({'full_frozen_SQL_checks':checks,'limit':'This checks these SQLite inputs; it is not raw-source semantic certification.'}))


if __name__=='__main__':main()

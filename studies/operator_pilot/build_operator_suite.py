#!/usr/bin/env python3
"""Build a protocol-fixed authored analytical pilot with Python/SQL gold agreement."""
from pathlib import Path
import argparse,collections,gzip,hashlib,itertools,json,sqlite3,time

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def js(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def q(x):return "'"+x.replace("'","''")+"'"
def norm(rows):return sorted(set(tuple(str(v)for v in row)for row in rows))
def number(cr):return cr.removeprefix('tdoc:')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--databases',type=Path,required=True);a=ap.parse_args()
 protocol=Path(__file__).with_name('protocol.json');pr=json.loads(protocol.read_text());assert len(pr['operators'])==6
 a.out.mkdir(parents=True,exist_ok=False);a.databases.mkdir(parents=True,exist_ok=True)
 items=[];public=[];coverage=[];inputs=[];timings=[];schemas={}
 for wi,wg in enumerate(pr['partitions']):
  tick=time.monotonic();plain=a.release/'sqlite'/f'{wg}.sqlite';src=plain if plain.exists()else plain.with_suffix('.sqlite.gz')
  before=sha(src);db=src
  if src.suffix=='.gz':
   db=a.databases/f'{wg}.sqlite'
   if not db.exists():
    with gzip.open(src,'rb')as f,db.open('xb')as out:
     for block in iter(lambda:f.read(1<<20),b''):out.write(block)
  c=sqlite3.connect('file:'+str(db.resolve())+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON')
  schema=[r[0]for r in c.execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL ORDER BY type,name")]
  domains={k:[r[0]for r in c.execute('SELECT DISTINCT '+k+' FROM disposition ORDER BY '+k)]for k in ['scope','evidence_status','code']}
  assert 'whole_target'in domains['scope'] and 'source_verified'in domains['evidence_status']
  schemas[wg]={'sql':schema,'disposition_value_domains':domains,'identifier_convention':'Document identifiers prefix tdoc:; pack identifiers prefix tdoc:crpack/; section identifiers prefix tdoc:section/ followed by specification-release-clause. Questions request display values rather than prefixed identifiers.'}
  members=collections.defaultdict(set)
  for cr,pack in c.execute('SELECT cr,pack_id FROM cr_in_pack'):members[pack].add(cr)
  sections={r[0]:tuple(r[1:])for r in c.execute('SELECT id,spec,release,clause FROM section')}
  links=collections.defaultdict(set);missing=0
  for cr,sid in c.execute('SELECT cr,section_id FROM cr_modifies_section'):
   if sid not in sections:missing+=1
   else:links[cr].add(sid)
  assert missing==0,('Dangling section targets',wg,missing)
  codes=collections.defaultdict(set)
  for cr,code in c.execute("SELECT target,code FROM disposition WHERE evidence_status='source_verified' AND scope='whole_target'"):codes[cr].add(code)
  packs={r[0]:r[1]for r in c.execute('SELECT id,pack_number FROM cr_pack')}
  pools={v['family']:[]for v in pr['operators']}
  for pack,crs in sorted(members.items()):
   assert pack in packs
   if len({cr for cr in crs if codes[cr]})>=2:pools['pack_disposition_counts'].append((pack,))
   sizes={len(links[cr])for cr in crs}
   if len(crs)>=2 and len({s for s in sizes if s>0})>=2:pools['largest_clause_footprint'].append((pack,))
   if 0 in sizes and any(s>0 for s in sizes):pools['members_without_clause_records'].append((pack,))
   bysec=collections.defaultdict(set)
   for cr in crs:
    for sid in links[cr]:bysec[sid].add(cr)
   pairs=set()
   for peers in bysec.values():pairs.update(itertools.combinations(sorted(peers),2))
   for first,second in sorted(pairs):
    inter=links[first]&links[second]
    if inter and (links[first]|links[second])-inter:
     pools['shared_clauses'].append((pack,first,second))
     if links[first]-links[second]:pools['exclusive_clauses'].append((pack,first,second))
   spairs=set()
   for cr in crs:spairs.update(itertools.combinations(sorted(links[cr]),2))
   for one,two in sorted(spairs):
    if bysec[one]&bysec[two] and bysec[one]^bysec[two]:pools['both_clause_documents'].append((pack,one,two))
  for definition in pr['operators']:
   family=definition['family'];pool=pools[family]
   digest=lambda candidate:hashlib.sha256(js(['Source-bound analytical operator pilot',wg,family,candidate]).encode()).hexdigest()
   candidate=min(pool,key=digest)if pool else None
   coverage.append({'wg':wg,'family':family,'eligible_candidates':len(pool),'candidate_identity_order_sha256':hashlib.sha256('\n'.join(js(v)for v in sorted(pool)).encode()).hexdigest(),'selected':candidate,'selection_sha256':digest(candidate)if candidate else None})
   if candidate is None:continue
   pack=candidate[0];packnum=packs[pack];crs=members[pack];packlit=q(pack)
   if family=='pack_disposition_counts':
    groups=collections.defaultdict(set)
    for cr in crs:
     for code in codes[cr]:groups[code].add(number(cr))
    gold=[(code,len(group))for code,group in groups.items()];fields=['disposition','document_count']
    sql=f"SELECT d.code,COUNT(DISTINCT REPLACE(m.cr,'tdoc:','')) FROM cr_in_pack m JOIN disposition d ON d.target=m.cr WHERE m.pack_id={packlit} AND d.evidence_status='source_verified' AND d.scope='whole_target' GROUP BY d.code"
    templates=[f"For CR pack {packnum}, how many distinct {wg} member documents have each source-verified whole-document disposition? Return the disposition code and its distinct-document count. A document with several recorded codes counts once in each relevant group.",f"Summarize pack {packnum} by recorded {wg} outcome. Count distinct member documents for every source-verified disposition applying to the whole document, returning code and count; count a multi-code document in each code group.",f"I need a disposition histogram for the {wg} documents in {packnum}: for each source-verified whole-document code, give the code and the number of different documents carrying it. Include each document once per code.",f"Group the members of {packnum} by their {wg} source-verified whole-document disposition. Report each code with its distinct document total; a document may belong to several code groups.",f"Count the {wg} documents in CR pack {packnum} separately for each source-verified whole-document disposition code. Return code and distinct document count, allowing a document to contribute to several codes."]
   elif family in ('shared_clauses','exclusive_clauses'):
    first,second=candidate[1:];shared=family=='shared_clauses';chosen=links[first]&links[second]if shared else links[first]-links[second];gold=[sections[sid]for sid in chosen];fields=['specification','release','clause']
    op='INTERSECT'if shared else'EXCEPT'
    sql=f"SELECT s.spec,s.release,s.clause FROM cr_modifies_section x JOIN section s ON s.id=x.section_id WHERE x.cr={q(first)} {op} SELECT s.spec,s.release,s.clause FROM cr_modifies_section x JOIN section s ON s.id=x.section_id WHERE x.cr={q(second)}"
    condition='both documents modify'if shared else f"{number(first)} modifies and {number(second)} does not modify in the released records"
    templates=[f"Compare {number(first)} with {number(second)} from pack {packnum}. Return the specification, release and clause for each typed section that {condition}.",f"Looking at the typed clause links for {number(first)} and {number(second)}, list specification, release and clause for the sections that {condition}.",f"For the two pack-{packnum} documents {number(first)} and {number(second)}, which typed sections satisfy this condition: {condition}? Give specification, release and clause.",f"Audit the clause sets of {number(first)} and {number(second)} in {packnum}. Report specification, release and clause exactly when {condition}.",f"Use the recorded section links of {number(first)} and {number(second)} to find every section that {condition}. Return its specification, release and clause, preserving release distinctions."]
   elif family=='both_clause_documents':
    one,two=candidate[1:];gold=[(number(cr),)for cr in crs if {one,two}<=links[cr]];fields=['document']
    sql=f"SELECT REPLACE(m.cr,'tdoc:','') FROM cr_in_pack m WHERE m.pack_id={packlit} AND EXISTS(SELECT 1 FROM cr_modifies_section x WHERE x.cr=m.cr AND x.section_id={q(one)}) AND EXISTS(SELECT 1 FROM cr_modifies_section y WHERE y.cr=m.cr AND y.section_id={q(two)})"
    label=lambda sid:f"TS {sections[sid][0]} {sections[sid][1]} clause {sections[sid][2]}"
    a1,a2=label(one),label(two)
    templates=[f"Which {wg} documents in {packnum} have typed modification links to both {a1} and {a2}? Return the document numbers; each result must cover both named sections.",f"Find members of CR pack {packnum} that modify each of these sections: {a1}; {a2}. Report {wg} document numbers, requiring both links for every result.",f"I need the {wg} documents in {packnum} whose recorded clause footprint includes {a1} as well as {a2}. Return only their document numbers.",f"Filter CR pack {packnum} to {wg} member documents linked to both {a1} and {a2}. Give each document number once.",f"Within {packnum}, list the {wg} document numbers that modify both {a1} and {a2} according to the typed links. Matching just one section is insufficient."]
   elif family=='largest_clause_footprint':
    counts={cr:len(links[cr])for cr in crs};high=max(counts.values());gold=[(number(cr),n)for cr,n in counts.items()if n==high];fields=['document','clause_count']
    sql=f"WITH counts AS (SELECT m.cr,COUNT(DISTINCT x.section_id) AS n FROM cr_in_pack m LEFT JOIN cr_modifies_section x ON x.cr=m.cr WHERE m.pack_id={packlit} GROUP BY m.cr) SELECT REPLACE(cr,'tdoc:',''),n FROM counts WHERE n=(SELECT MAX(n)FROM counts)"
    templates=[f"Among the {wg} members of CR pack {packnum}, which documents have the largest number of distinct typed modified-section identities? Return every tied document number with its count; different releases count as different identities.",f"Rank the {wg} documents in {packnum} by the count of distinct typed sections they modify. Give all documents tied at the maximum, returning document number and count, with releases kept distinct.",f"Which {wg} member of {packnum} has the widest recorded clause footprint? Count distinct typed section identities, preserving releases, and return every document tied for first place with its count.",f"For pack {packnum}, count typed modified sections per {wg} member document, treating different releases separately. Return document number and count for all documents attaining the maximum.",f"Find the largest distinct-section count among {wg} members of {packnum}. Report every document number with that count, including ties and preserving release distinctions in the section count."]
   else:
    gold=[(number(cr),)for cr in crs if not links[cr]];fields=['document']
    sql=f"SELECT DISTINCT REPLACE(m.cr,'tdoc:','') FROM cr_in_pack m WHERE m.pack_id={packlit} AND NOT EXISTS(SELECT 1 FROM cr_modifies_section x WHERE x.cr=m.cr)"
    templates=[f"Which {wg} member documents of pack {packnum} have zero typed modified-section links in the released records? Return document numbers. This asks about recorded-link absence in this snapshot.",f"List {wg} members of CR pack {packnum} for which the released snapshot records no typed clause-modification link. Give document numbers; the condition concerns the records, rather than the contents of the standards.",f"Audit pack {packnum} for {wg} documents lacking any typed modified-section record in this snapshot. Return their document numbers.",f"From the {wg} members of {packnum}, return the document numbers with no outgoing typed modification link to a section in the released records.",f"Identify {wg} documents in {packnum} whose recorded typed-section footprint is empty. Return their document numbers, interpreting emptiness within this released snapshot."]
   gold=norm(gold);deadline=time.monotonic()+60;c.set_progress_handler(lambda:time.monotonic()>deadline,10000)
   result=norm(c.execute(sql).fetchall());c.set_progress_handler(None,0)
   if gold!=result:raise ValueError((wg,family,'Python/SQL disagreement',gold,result))
   item={'id':f'{wg}-analytic-{family}','wg':wg,'family':family,'question':templates[wi],'fields':fields,'authorship':'author-written analytical task','selection_sha256':digest(candidate),'anchor':candidate,'gold':gold,'reference_sql':sql,'python_sql_agreement':True}
   items.append(item);public.append({k:item[k]for k in ['id','wg','question','fields','authorship']})
  c.close();assert sha(src)==before
  inputs.append({'wg':wg,'source':str(src),'source_sha256':before,'database':str(db),'database_sha256':sha(db),'source_unchanged':True});timings.append({'wg':wg,'seconds':time.monotonic()-tick})
 save(a.out/'selection_and_gold.json',{'protocol_sha256':sha(protocol),'items':items,'selection':coverage,'inputs':inputs,'execution':timings,'reference_sqlite':sqlite3.sqlite_version,'source_inputs_unchanged':True})
 save(a.out/'writer_questions.json',{'condition':'Schema and full value domains; first responses; no execution feedback','questions':public})
 save(a.out/'writer_schema.json',schemas)
 save(a.out/'freeze.json',{'protocol_sha256':sha(protocol),'builder_sha256':sha(Path(__file__)),'files':{p.name:sha(p)for p in a.out.glob('*.json')},'items':len(items),'question_authorship':'author-written, not independently collected engineer questions','model_outputs_exist':False})
 print(js({'items':len(items),'cells':len(coverage),'missing_cells':[x for x in coverage if x['selected']is None],'source_inputs_unchanged':True,'python_sql_agreement':all(x['python_sql_agreement']for x in items)}))
if __name__=='__main__':main()

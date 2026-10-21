"""Independent SQL expression of the retained-field approval grammar.

SQLite functions registered here perform lexical string operations only.
Document roles, temporal scope, target binding and membership are SQL
expressions over the immutable original tables and query-local CTEs.
"""
import functools
import json
import re
from declarative_grammar import *


def q(value):
    if value is None:return 'NULL'
    if value is True:return '1'
    if value is False:return '0'
    if isinstance(value,(int,float)):return str(value)
    return "'"+str(value).replace("'","''")+"'"
def rxsql(text,pattern):return 'regexp('+q(pattern)+','+text+')'
def co(text):return 'coalesce('+text+",'')"
def bothsql(*values):return '('+' AND '.join(values)+')'
def eithersql(*values):return '('+' OR '.join(values)+')'
def notsql(value):return '(NOT '+value+')'
def jpath(name,key):return "coalesce(json_extract("+name+','+q('$.'+key)+"),'')"
def sql(expr,names=None):
    names=names or {};render=lambda x:sql(x,names);op,*args=expr
    if op=='var':return names.get(args[0],'e.'+args[0])
    if op=='lit':return q(args[0])
    if op=='rx':return rxsql(render(args[0]),args[1])
    if op=='and':return bothsql(*(render(x)for x in args))
    if op=='or':return eithersql(*(render(x)for x in args))
    if op=='not':return notsql(render(args[0]))
    if op=='any':
        alias=args[1]
        return 'EXISTS(SELECT 1 FROM json_each('+render(args[0])+') AS '+alias+' WHERE '+sql(args[2],dict(names,**{alias:alias+'.value'}))+')'
    if op=='eq':return '('+render(args[0])+'='+render(args[1])+')'
    if op=='in':return 'EXISTS(SELECT 1 FROM json_each('+render(args[1])+') AS contained WHERE contained.value='+render(args[0])+')'
    if op=='prop':return jpath(render(args[0]),args[1])
    if op=='dynamic_rx':return 'regexp('+render(args[1])+','+render(args[0])+')'
    if op=='concat':return '('+'||'.join(render(x)for x in args)+')'
    raise ValueError(op)


def register_lexical(db):
    @functools.lru_cache(maxsize=1024)
    def compiled(pattern):return re.compile(pattern)
    def regex(pattern,text):return int(bool(compiled(pattern).search(text or '')))
    def js(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
    @functools.lru_cache(maxsize=4096)
    def lines(text):return js((text or '').splitlines())
    def get_line(array,index):
        values=json.loads(array)
        return values[index] if 0<=index<len(values)else ''
    def join_lines(array,start,end):return '\n'.join(json.loads(array)[start:end])
    def captures(pattern,text):
        values=compiled(pattern).findall(text or '')
        if any(isinstance(x,tuple)for x in values):raise ValueError('one lexical capture group required')
        return js(values)
    def before(pattern,text):return compiled(pattern).split(text or '',maxsplit=1)[0]
    def first_spec(text):
        found=re.search(SPEC,text or '')
        return re.sub(r'\s','',found[0])[-3:] if found else ''
    def title_key(text):
        return re.sub(r'(?i)^(?:(?:draft|final)\s+)?(?:CR|FLS\s*#?\s*\d+)(?:\s+(?:on|for))?\s*','',re.sub(r'\s+',' ',(text or '').replace('\u00a0',' ')).strip()).lower()
    funcs={
        'regexp':(2,regex),'split_lines':(1,lines),'line_at':(2,get_line),'lines_text':(3,join_lines),
        'captures':(2,captures),'before_regex':(2,before),'first_spec':(1,first_spec),
        'normalize_text':(1,lambda x:re.sub('[^a-z0-9]','',(x or '').lower())),
        'title_key':(1,title_key),'strip_prefix':(2,lambda p,t:re.sub(p,'',t or '')),
        'ids_json':(1,lambda x:js(sorted(set(re.findall(r'R1-\d{7}(?!\d)',x or ''))))),
        'sentence_clauses':(1,lambda x:js(re.split(r'(?<=[.!?;])\s+(?=[A-Z])',x or '')))}
    for name,(arity,fun)in funcs.items():db.create_function(name,arity,fun,deterministic=True)
    return sorted(funcs)


SUBJECT=r'(?i)\b(?:with\s+(?:a|the)\s+change\s+of|(?:cross[- ]?)?reference\s+to)\b'
CLAUSE=r'(?i)\bclauses?\s+(\d+(?:\.\d+)*[a-z]?)'
SECTION=r'(?i)\b(?:clauses?|sections?)\s+(\d+(?:\.\d+)*[a-z]?)'
SELECTOR=r'(?i)\b(?:TP|text proposal)\s*#?\s*([a-z]|\d+(?:-\d+)*(?:[a-z])?(?:-v\d+)?)\b'
DECL_START=r'(?i)^(?:\|\s*)?[-_<=>\s]*(?:(?:Start|Begin|Text)\s*(?:of\s*)?(?:the\s*)?)?(?:TP(?:s)?(?=\b|[0-9#_])|Text\s+Proposal(?:s)?)(?:\b|(?=[0-9#_]))'
DECL_BARE=r'(?i)^(?:\|\s*)?[-_<=>\s]*(?:TS\s*)?38\s*\.\s*\d{3}(?!\d)\b'

def capture(pattern,text):return 'captures('+q(pattern)+','+text+')'
def declared(text):
    first=rxsql('trim('+text+')',DECL_START)
    segment='before_regex('+q(r'(?i)\b(?:with\s+(?:a|the)\s+change\s+of|cross[- ]?reference|reference\s+to|unchanged)\b')+','+text+')'
    return eithersql(bothsql(first,rxsql(segment,TS)),bothsql(rxsql('trim('+text+')',DECL_BARE),'first_spec('+text+")='214'"))

def compatible(line,summary):
    subject='before_regex('+q(r'(?i)\bwith\s+(?:a\s+)?change\s+of\b')+','+line+')'
    own=capture(CLAUSE,line);other=capture(SECTION,summary)
    sx=capture(SELECTOR,line);sy=capture(SELECTOR,summary)
    return bothsql(eithersql(notsql(rxsql(subject,r'(?i)(?:TS\s*)?(?:37|38)\s*\.\s*\d{3}(?!\d)')),rxsql(subject,TS)),
        eithersql('json_array_length('+own+')=0','json_array_length('+other+')=0',
            'EXISTS(SELECT 1 FROM json_each('+own+') x,json_each('+other+") y WHERE lower(x.value)=lower(y.value) OR lower(x.value) LIKE lower(y.value)||'.%' OR lower(y.value) LIKE lower(x.value)||'.%' OR lower(x.value)=lower(y.value)||'a' OR lower(y.value)=lower(x.value)||'a')"),
        eithersql('json_array_length('+sx+')=0','json_array_length('+sy+')=0',
            'EXISTS(SELECT 1 FROM json_each('+sx+') x,json_each('+sy+') y WHERE lower(x.value)=lower(y.value))'))


def prefix():
    named=lambda text:'SELECT value FROM json_each(ids_json('+text+'))'
    full="coalesce(a.content,'')||char(10)||coalesce(a.contentWithEquations,'')||char(10)||coalesce(a.note,'')"
    doc_json="""json_object('tdocNumber',d.tdocNumber,'title',d.title,'type',d.type,'secretaryRemarks',d.secretaryRemarks,
       'typed214',EXISTS(SELECT 1 FROM targets t WHERE t.node_id=d.node_id),
       'targetNumber',coalesce((SELECT CAST(CAST(t.crNumber AS INTEGER)AS TEXT) FROM targets t WHERE t.node_id=d.node_id),''))"""
    return """
WITH
targets AS MATERIALIZED(SELECT DISTINCT c.* FROM CR c JOIN rel_MODIFIES m ON m.src_id=c.node_id JOIN Spec s ON s.node_id=m.dst_id WHERE s.specNumber='38.214'),
events AS MATERIALIZED(SELECT DISTINCT src_id,dst_id FROM edge WHERE rel_type IN('PRESENTED_AT','MADE_AT')),
target_lines AS MATERIALIZED(SELECT t.node_id,t.title,j.key line0,j.value line FROM targets t,json_each(split_lines(coalesce(t.summaryOfChange,''))) j),
reverse_components AS MATERIALIZED(
 SELECT DISTINCT d.tdocNumber,l.node_id target_id,l.line FROM target_lines l,json_each(ids_json(l.line)) ident JOIN Tdoc d ON d.tdocNumber=ident.value
 WHERE EXISTS(SELECT 1 FROM events de JOIN events ce ON de.dst_id=ce.dst_id WHERE de.src_id=d.node_id AND ce.src_id=l.node_id)),
same_title AS MATERIALIZED(
 SELECT DISTINCT d.tdocNumber,t.node_id target_id FROM Tdoc d JOIN targets t ON title_key(d.title)=title_key(t.title)
 WHERE d.type IN('discussion','Discussion') AND """+rxsql("coalesce(d.title,'')",r'(?i)^FLS\s*#?\s*\d+')+"""
 AND EXISTS(SELECT 1 FROM events de JOIN events ce ON de.dst_id=ce.dst_id WHERE de.src_id=d.node_id AND ce.src_id=t.node_id)),
combined_components AS MATERIALIZED(
 SELECT ident.value tdocNumber,l.node_id target_id,l.line FROM target_lines l,json_each(ids_json(l.line)) ident
 WHERE """+rxsql("coalesce(l.title,'')",r'(?i)combined.*CR')+' AND '+rxsql('l.line',TS)+""" AND l.line LIKE ident.value||' %'),
all_records AS MATERIALIZED(SELECT a.*,"""+full+""" AS "full" FROM Agreement a),
record_docs AS MATERIALIZED(
 SELECT DISTINCT a.node_id owner_id,d.*,"""+doc_json+""" doc_json FROM all_records a,json_each(ids_json(a.full)) ident JOIN Tdoc d ON d.tdocNumber=ident.value),
candidate AS MATERIALIZED(
 SELECT a.* FROM all_records a WHERE """+rxsql('a.full',TS)+"""
 OR EXISTS(SELECT 1 FROM record_docs d WHERE d.owner_id=a.node_id AND (
 EXISTS(SELECT 1 FROM targets t WHERE t.node_id=d.node_id)
 OR """+rxsql("coalesce(d.title,'')",TS)+' OR '+rxsql("coalesce(d.secretaryRemarks,'')",TS)+"""
 OR EXISTS(SELECT 1 FROM reverse_components rc WHERE rc.tdocNumber=d.tdocNumber)
 OR EXISTS(SELECT 1 FROM same_title st WHERE st.tdocNumber=d.tdocNumber)
 OR EXISTS(SELECT 1 FROM combined_components cc WHERE cc.tdocNumber=d.tdocNumber)))),
fields AS MATERIALIZED(
 SELECT a.*, 'content' fieldName,coalesce(a.content,'') fieldText,split_lines(a.content) lines FROM candidate a
 UNION ALL SELECT a.*,'contentWithEquations',coalesce(a.contentWithEquations,''),split_lines(a.contentWithEquations) FROM candidate a
 UNION ALL SELECT a.*,'note',coalesce(a.note,''),split_lines(a.note) FROM candidate a),
field_scope AS MATERIALIZED(
 SELECT f.*,coalesce((SELECT min(j.key)FROM json_each(f.lines)j WHERE """+rxsql('j.value',HEADER)+"""),json_array_length(f.lines)) cut,
 line_at(f.lines,0) firstLine,
 coalesce((SELECT j.value FROM json_each(split_lines(f.content))j WHERE trim(j.value)<>'' ORDER BY j.key LIMIT 1),'')firstContent
 FROM fields f),
field_context AS MATERIALIZED(
 SELECT f.*,lines_text(f.lines,0,f.cut) ownText,
 (SELECT d.doc_json FROM record_docs d WHERE d.owner_id=f.node_id AND d.tdocNumber IN("""+named('line_at(f.lines,f.cut)')+""") LIMIT 1)firstDocument,
 coalesce((SELECT j.value FROM json_each(f.lines)j WHERE trim(j.value)<>'' ORDER BY j.key LIMIT 1),'')firstNonempty
 FROM field_scope f),
line_context AS MATERIALIZED(
 SELECT f.*,j.key line0,j.value l, """+'before_regex('+q(SUBJECT)+',j.value)'+""" subject,
 line_at(f.lines,j.key-1)prev,line_at(f.lines,j.key+1)next,
 lines_text(f.lines,j.key+1,j.key+20)following20,lines_text(f.lines,j.key+1,j.key+5)following4,
 lines_text(f.lines,0,max(0,j.key-1))beforePrev,first_spec(j.value)firstTarget,j.key<=2 firstThreeLines,
 coalesce((SELECT ident.value FROM json_each(f.lines)h,json_each(ids_json(h.value))ident WHERE h.key<=j.key AND """+rxsql('h.value',HEADER)+""" ORDER BY h.key DESC LIMIT 1),'')currentHeader,
 coalesce((SELECT json_group_array(json(d.doc_json)) FROM record_docs d WHERE d.owner_id=f.node_id AND d.tdocNumber IN("""+named('j.value')+""")),'[]')lineDocs
 FROM field_context f,json_each(f.lines)j)
"""


def features():
    lines=lambda alias:'json_each(e.lines) '+alias
    named=lambda text:'SELECT value FROM json_each(ids_json('+text+'))'
    named_docs=lambda condition:'EXISTS(SELECT 1 FROM record_docs d WHERE d.owner_id=e.node_id AND d.tdocNumber IN('+named('e.l')+') AND '+condition+')'
    direct="EXISTS(SELECT 1 FROM targets t WHERE t.node_id=d.node_id)"
    firsttyped=jpath('e.firstDocument','typed214')+'=1'
    firstremarks=jpath('e.firstDocument','secretaryRemarks')
    firsttitle=jpath('e.firstDocument','title')
    targetcontext=eithersql(firsttyped,bothsql(rxsql(firstremarks,TS),rxsql(firstremarks,CR),rxsql(firstremarks,TP)),bothsql(rxsql(firsttitle,CR),rxsql('e.ownText',TS)))
    adjacency=bothsql('e.cut>0','e.cut<json_array_length(e.lines)',targetcontext,
        notsql(bothsql(rxsql('e.ownText',r'(?i)^\s*(?:Endorse|The draft|The final|Send|Approve).*\bLS\b'),notsql(rxsql('e.ownText',NORM)))),
        notsql(bothsql(rxsql('e.firstLine',r'(?:37|38)\s*\.\s*\d{3}'),notsql(rxsql('e.firstLine',TS)),eithersql(rxsql('e.firstLine',STATE),rxsql('e.firstLine',TP)))),
        'NOT EXISTS(SELECT 1 FROM '+lines('x')+' WHERE x.key<e.cut AND '+rxsql('x.value',r'(?i)^\s*Follow\s*up\s+discussion\b')+')',
        eithersql(rxsql('e.ownText',NORM),bothsql(rxsql('e.ownText',STATE),rxsql('e.ownText',TP),rxsql('e.ownText',r'(?i)cover\s*sheet\s+of\s+the\s+CR'))),
        eithersql(notsql(rxsql('e.ownText',r'(?:37|38)\s*\.\s*\d{3}')),rxsql('e.ownText',TS)),notsql(rxsql('e.firstLine',BAD)))
    shared=lambda target:'EXISTS(SELECT 1 FROM events ae JOIN events ce ON ae.dst_id=ce.dst_id WHERE ae.src_id=e.node_id AND ce.src_id='+target+')'
    cleanTitle="trim(strip_prefix("+q(r'(?i)^\s*(?:(?:Draft|Final)\s+)*(?:CRs?)\s+(?:on|for|to)\s*')+",coalesce(t.title,'')))"
    complete=bothsql("e.firstLine<>''",rxsql('e.firstLine',NORM),notsql(rxsql('e.firstLine',BAD)),
        'EXISTS(SELECT 1 FROM targets t WHERE '+shared('t.node_id')+' AND '+cleanTitle+"<>'' AND instr(normalize_text(e.firstLine),normalize_text("+cleanTitle+'))>0)')
    combined=bothsql(rxsql(co('e.content'),TS),rxsql(co('e.content'),r'(?i)\b(?:UE|gNB)\b.{0,40}\b(?:expected|shall|should|follows|is configured|is provided)\b'),
        'EXISTS(SELECT 1 FROM record_docs d JOIN combined_components cc ON cc.tdocNumber=d.tdocNumber WHERE d.owner_id=e.node_id AND '+shared('cc.target_id')+')')
    applicability="normalize_text(coalesce(json_extract(captures("+q(r'(?i)^\s*For\s+(?:a|an|the)\s+(.+?)\s+when\b')+",e.firstContent),'$[0]'),''))"
    captured_scope=bothsql(applicability+"<>''",rxsql(co('e.content'),NORM_FOLLOW),notsql(rxsql('e.firstLine',BAD)),
        'EXISTS(SELECT 1 FROM record_docs d JOIN reverse_components rc ON rc.tdocNumber=d.tdocNumber WHERE d.owner_id=e.node_id AND '+rxsql('rc.line',r'(?i)\bcapture\s+the\s+agreements?\b')+' AND instr(normalize_text(rc.line),'+applicability+')>0)')
    firstcomplete=bothsql(eithersql(bothsql(declared('e.firstNonempty'),rxsql('e.firstNonempty',DECL_START)),
        bothsql(rxsql('e.firstNonempty',r'(?i)^\s*Reasons?\s+for\s+change'),
        'EXISTS(SELECT 1 FROM '+lines('x')+' WHERE '+rxsql('x.value',r'(?i)(?:Start|Begin).{0,20}(?:text\s*proposal|TP)')+')',
        'EXISTS(SELECT 1 FROM '+lines('x')+' WHERE '+rxsql('x.value',r'(?i)^\s*Summary\s+(?:of|for)\s+change')+')',
        eithersql('EXISTS(SELECT 1 FROM '+lines('x')+' WHERE '+declared('x.value')+')',"first_spec(e.firstNonempty)='214'"))),
        'NOT EXISTS(SELECT 1 FROM '+lines('x')+' WHERE '+rxsql('x.value',r'(?i)\bno consensus\b.*\b(?:TP|text proposal)\b|\b(?:TP|text proposal).{0,40}\b(?:not agreed|not endorsed|not approved)\b')+')')
    def prior(opener,reset):
        return 'EXISTS(SELECT 1 FROM '+lines('op')+' WHERE op.key<e.line0 AND '+opener+' AND NOT EXISTS(SELECT 1 FROM '+lines('bt')+' WHERE bt.key>op.key AND bt.key<e.line0 AND '+reset+'))'
    header=lambda text:rxsql(text,HEADER)
    listopen=r'(?i)(?:following\s+(?:final\s+)?CRs?.{0,80}\b(?:agreed|endorsed|approved)|(?:final|draft)\s*CRs?.{0,60}\b(?:agreed|endorsed|approved).{0,20}\bin\s*:)|agreed\s+(?:TPs?|text proposals?).{0,150}(?:following|draft\s*CR)|(?:draft\s*CR).{0,80}endorsed\s+in\s*:'
    allowlist=r'(?i)^\s*(?:\(?(?:Rel-|TS\s*38)|R1-\d|[,;]|MCC\b|(?:The )?spec(?:ification)? editor)'
    longopen=r'(?i)^\s*(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday)(?:\s+decision)?:\s*)?(?:The\s+)?(?:following\s+(?:(?:final|draft|alignment)\s+)?CRs?\s+(?:are\s+)?(?:agreed|endorsed|approved)|agreed\s+text\s+proposals?.*captured\s+in\s+the\s+following.*draft\s+CRs?)'
    longend=r'(?i)^\s*(?:Discussion:|Issue\s*#?\d|Decision:|No\s+(?:agreement|consensus)|Noted\b|For\s+further\s+study|Comeback\b)'
    control=r'(?i)^\s*(?:Discussion:|No\s+(?:agreement|consensus)|Come\s*back\b|For\s+(?:future|further)\b|From\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday)\b)'
    approvedend=r'(?i)^\s*(?:Discussion:|Issue\s*#?\d|No\s+(?:consensus|agreement)|Noted\b|Comeback\b|Come\s+back\b|Reason\s+for\s+change|Consequences\s+if\s+not\s+approved)'
    approvednow=r'(?i)\b(?:is|are)\s+(?:agreed|endorsed|approved|adopted|agreeable)|^\s*(?:Agree\s+on|Adopt|Endorse|Approve|Accept)\b'
    targetnamed=named_docs(direct)
    listed=bothsql(header('e.l'),targetnamed,prior(bothsql(notsql(rxsql('op.value',BAD)),rxsql('op.value',listopen)),bothsql(notsql(header('bt.value')),"trim(bt.value)<>''",notsql(rxsql('bt.value',allowlist)))))
    longlisted=bothsql(header('e.l'),targetnamed,prior(bothsql(rxsql('op.value',longopen),notsql(rxsql('op.value',r'(?i)not\s+(?:agreed|endorsed|approved)'))),rxsql('bt.value',longend)))
    approvedlist=bothsql(targetnamed,eithersql(rxsql('e.l',TS),notsql(rxsql('e.l',r'(?i)\b(?:TS\s*)?\d{2}\.\d{3}\b'))),
        prior(bothsql(rxsql('op.value',r'(?i)following\s+(?:editorial\s+changes|text\s+proposals?|TPs?)'),eithersql(rxsql('op.value',approvednow),bothsql(rxsql('op.value',CR),rxsql('op.value',r'(?i)include\s+(?:them|these)'))),notsql(rxsql('op.value',BAD))),eithersql(header('bt.value'),rxsql('bt.value',approvedend))))
    opening="(op.value||CASE WHEN op.key+1<e.line0 AND "+rxsql('line_at(e.lines,op.key+1)',r'(?i)^\s*(?:To\s+be\s+included|For\s+inclusion)')+" THEN ' '||line_at(e.lines,op.key+1) ELSE '' END)"
    editorlist=bothsql(rxsql('e.l',r'(?i)^\s*(?:(?:First|Second|Third|Fourth)\s+)?(?:TP(?:\s*#?\s*\d+(?:-\d+)*[A-Za-z]?)?|text\s+proposal|draft\s+proposal)\b'),rxsql('e.l',TS),notsql(rxsql('e.l',BAD)),
        prior(bothsql(rxsql('op.value',STATE),notsql(rxsql('op.value',BAD)),rxsql('op.value',TP),rxsql('op.value',r'(?i)\b(?:following|all)\b'),
        rxsql(opening,r'(?i)(?:alig(?:n)?ment.{0,30}\bCRs?\b|editor.{0,30}\bCRs?\b|\bCRs?\b.{0,30}alig(?:n)?ment)'),
        notsql(rxsql(opening,r'(?i)\b(?:comeback|come\s+back|to\s+be\s+(?:drafted|prepared)|will\s+prepare)\b')),eithersql(notsql(rxsql(opening,SPEC)),rxsql(opening,TS))),eithersql(header('bt.value'),rxsql('bt.value',control))))
    alignscope=lambda text:bothsql(rxsql(text,r'(?i)^\s*For\s+alignment\b'),rxsql(text,CR),rxsql(text,SPEC))
    scoped=bothsql(rxsql('e.l',STATE),notsql(rxsql('e.l',BAD)),rxsql('e.l',r'(?i)\b(?:TP(?:s|\s*#?\s*\d+(?:-\d+)*[A-Za-z]?)?|text\s+proposals?|draft\s+proposals?|editorial\s+corrections?)\b'),eithersql(notsql(rxsql('e.l',SPEC)),rxsql('e.l',TS)),
        prior(bothsql(alignscope('op.value'),rxsql('op.value',TS)),eithersql(header('bt.value'),rxsql('bt.value',control),alignscope('bt.value'))))
    def title_range(above):
        direction='h.key<e.line0' if above else 'h.key>e.line0'
        interval='bt.key>h.key AND bt.key<e.line0' if above else 'bt.key>e.line0 AND bt.key<h.key'
        return 'EXISTS(SELECT 1 FROM '+lines('h')+' WHERE '+direction+' AND '+header('h.value')+' AND EXISTS(SELECT 1 FROM record_docs d WHERE d.owner_id=e.node_id AND d.tdocNumber IN('+named('h.value')+') AND '+rxsql(co('d.title'),TS)+' AND '+rxsql(co('d.title'),r'(?i)\b(?:TP|text proposal)\b')+') AND NOT EXISTS(SELECT 1 FROM '+lines('bt')+' WHERE '+interval+' AND NOT '+header('bt.value')+' AND '+rxsql('bt.value',r'(?i)^\s*(?:Agreement|Decision|Endorse|Adopt)\b')+'))'
    selcomp=lambda x,y:eithersql('json_array_length('+capture(SELECTOR,y)+')=0','EXISTS(SELECT 1 FROM json_each('+capture(SELECTOR,x)+') sx,json_each('+capture(SELECTOR,y)+') sy WHERE lower(sx.value)=lower(sy.value))')
    sectioncomp=lambda x,y:eithersql('json_array_length('+capture(SECTION,x)+')=0','json_array_length('+capture(SECTION,y)+')=0','EXISTS(SELECT 1 FROM json_each('+capture(SECTION,x)+') sx,json_each('+capture(SECTION,y)+') sy WHERE lower(sx.value)=lower(sy.value))')
    docpick='(d.tdocNumber IN('+named('e.l')+') OR (NOT EXISTS(SELECT 1 FROM json_each(ids_json(e.l))) AND '+rxsql('e.l',r'(?i)^\s*(?:Decision|(?:Monday|Tuesday|Wednesday|Thursday|Friday) decision):')+' AND d.tdocNumber=e.currentHeader))'
    remarks=bothsql(eithersql(notsql(rxsql('e.subject',SPEC)),rxsql('e.subject',TS)),
        'EXISTS(SELECT 1 FROM record_docs d,json_each(split_lines(d.secretaryRemarks)) ds WHERE d.owner_id=e.node_id AND '+docpick+' AND '+rxsql('ds.value',TS)+' AND '+rxsql('ds.value',ALIGN)+' AND '+rxsql('ds.value',TP)+' AND '+selcomp('e.l','ds.value')+' AND '+sectioncomp('e.l','ds.value')+')')
    breakact=lambda text:bothsql(rxsql(text,r'(?i)^\s*(?:Decision:|Agreement(?:s)?\s*[:(]|\b(?:Adopt|Endorse|Approve|Accept|Agree)\b)'),rxsql(text,STATE),rxsql(text,TP))
    def declaration_range(above):
        direction='dd.key<e.line0' if above else 'dd.key>e.line0'
        interval='bt.key>=dd.key AND bt.key<e.line0' if above else 'bt.key>e.line0 AND bt.key<=dd.key'
        return 'EXISTS(SELECT 1 FROM '+lines('dd')+' WHERE '+direction+' AND '+declared('dd.value')+' AND NOT EXISTS(SELECT 1 FROM '+lines('bt')+' WHERE '+interval+' AND '+breakact('bt.value')+'))'
    selecteddecl=bothsql(rxsql('e.l',r'(?i)\b(?:adopt(?:s|ed|ing)?|endorse(?:s|d)?|accept(?:s|ed)?|approve(?:s|d)?|agree(?:d|s)?)\b'),rxsql('e.l',TP),notsql(rxsql('e.l',BAD)),notsql(declared('e.l')),notsql(rxsql('e.subject',TS)),
        notsql(rxsql('e.l',r'(?i)^\s*(?:Reason(?:s)?\s+for\s+change|Summary\s+(?:of|for)\s+change|Consequences?\s+if\s+not\s+approved)')),
        eithersql(bothsql(rxsql('e.l',r'(?i)\babove\b'),declaration_range(True)),bothsql(notsql(rxsql('e.l',r'(?i)\babove\b')),rxsql('e.l',r'(?i)\b(?:following|below|corresponding|next|these)\b'),declaration_range(False))))
    scalefollow=bothsql(rxsql('e.l',r'(?i)\bscale\b.+\bfollowing\b'),
        'EXISTS(SELECT 1 FROM '+lines('x')+' WHERE x.key>e.line0 AND '+rxsql('x.value',TS)+' AND NOT EXISTS(SELECT 1 FROM '+lines('bt')+' WHERE bt.key>e.line0 AND bt.key<=x.key AND '+eithersql(header('bt.value'),rxsql('bt.value',r'(?i)^\s*(?:Agreement|Decision)\b'))+'))')
    values=dict(
        ownNormativeExactCapturedScope=captured_scope,ownNormativeAdjacentTargetCR=adjacency,ownNormativeCompleteSameEventTitle=complete,ownNormativeNamedCombinedEntry=combined,firstOwnCompleteTargetTP=firstcomplete,
        explicitCurrentSpecificationUpdate=bothsql(rxsql(co('e.content'),TS),rxsql(co('e.note'),r'(?i)above agreements imply to update specification')),
        noLineIDs='json_array_length(ids_json(e.l))=0',
        headerTyped214='EXISTS(SELECT 1 FROM record_docs d JOIN targets t ON t.node_id=d.node_id WHERE d.owner_id=e.node_id AND d.tdocNumber=e.currentHeader)',
        targetNumberTuple='EXISTS(SELECT 1 FROM record_docs d JOIN targets t ON t.node_id=d.node_id WHERE d.owner_id=e.node_id AND t.crNumber IS NOT NULL AND regexp('+q(r'(?i)\bCR\s*#?\s*0*')+"||CAST(CAST(t.crNumber AS INTEGER)AS TEXT)||"+q(r'(?:\s*(?:rev|r)\s*\d+)?\b')+',e.l))',
        listedApproved214=listed,openedApprovedCRList214=longlisted,approvedTPList214=approvedlist,editorListComponent214=editorlist,
        namedTargetTPTitle=named_docs(bothsql(rxsql(co('d.title'),TS),rxsql(co('d.title'),r'(?i)\b(?:TP|text proposal|draft text)\b'))),
        followingTargetTPTitle=title_range(False),aboveTargetTPTitle=title_range(True),
        reverseCompatibleComponent=named_docs('EXISTS(SELECT 1 FROM reverse_components rc WHERE rc.tdocNumber=d.tdocNumber AND '+compatible('e.l','rc.line')+')'),
        headerReverseCompatibleComponent='EXISTS(SELECT 1 FROM reverse_components rc WHERE rc.tdocNumber=e.currentHeader AND '+compatible('e.l','rc.line')+')',
        namedRemarksCompatibleComponent=remarks,uniqueSameEventTitleCR=named_docs('(SELECT count(*)FROM same_title st WHERE st.tdocNumber=d.tdocNumber)=1'),
        selectedDeclaredTargetTP=selecteddecl,scopedAlignmentCRApproval=scoped,scaleFollowingTarget=scalefollow)
    return values


def build(projection='members'):
    if projection not in ('members','scalar'):raise ValueError(projection)
    feature=features()
    contexts=',contexts AS MATERIALIZED(SELECT e.*,\n'+',\n'.join(value+' AS '+name for name,value in feature.items())+'\nFROM line_context e)\n'
    normal=[sql(r['predicate'])for r in SURFACE_RULES if r.get('scope')!='uppercase_sentence_clause']+[sql(r['predicate'])for r in CONTEXT_RULES]
    rule=next(r for r in SURFACE_RULES if r.get('scope')=='uppercase_sentence_clause')
    clauses='EXISTS(SELECT 1 FROM json_each(sentence_clauses(e.l))clauseText WHERE '+sql(rule['predicate'],{'l':'clauseText.value','subject':'before_regex('+q(SUBJECT)+',clauseText.value)'})+')'
    return prefix()+contexts+',eligible AS(SELECT DISTINCT e.node_id,e.resolutionId FROM contexts e WHERE '+eithersql(clauses,*normal)+')\n'+('SELECT resolutionId FROM eligible ORDER BY resolutionId\n'if projection=='members'else'SELECT count(*)AS agrCount FROM eligible\n')

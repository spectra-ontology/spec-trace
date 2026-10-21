#!/usr/bin/env python3
import contextlib,io,json,os,pathlib,runpy,sys
sys.dont_write_bytecode=True
source=pathlib.Path(sys.argv[1]).resolve()
allowed=[source,pathlib.Path(os.__file__).resolve().parent]
counts={k:0 for k in ['audited_read_opens','network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']}
def hook(event,args):
    group=None
    if event.startswith(('socket.','urllib.','http.client.')):group='network_calls'
    elif event.startswith(('subprocess.','os.system','os.fork','os.exec','os.posix_spawn')):group='subprocess_calls'
    elif event.startswith('sqlite3.'):group='SQL_calls'
    if group:
        counts[group]+=1;raise RuntimeError('forbidden capability: '+event)
    if event=='open':
        name,mode,flags=args
        if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            counts['write_open_attempts']+=1;raise RuntimeError('write open forbidden')
        if isinstance(name,(str,bytes,os.PathLike)):
            path=pathlib.Path(os.fsdecode(name)).absolute()
            if not any(path==a or a in path.parents for a in allowed):
                counts['host_private_open_attempts']+=1;raise RuntimeError('outside evidence/stdlib: '+str(path))
            counts['audited_read_opens']+=1
sys.addaudithook(hook)
capture=io.StringIO()
with contextlib.redirect_stdout(capture):runpy.run_path(str(source/'reproduce.py'),run_name='__main__')
result=json.loads(capture.getvalue());result['default_no_host_audit']=counts
print(json.dumps(result,ensure_ascii=False,sort_keys=True))

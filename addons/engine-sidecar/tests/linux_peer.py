"""Authored process peers: no application, credentials, assets or inference."""
import json
import os
import signal
import subprocess
import sys
import time

mode=sys.argv[1]
if mode=='exit': sys.exit(0)
if mode=='stalled':
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    time.sleep(60)
    sys.exit(0)
for line in sys.stdin:
    request=json.loads(line)
    if mode=='oversize':
        print('x'*65537,flush=True)
        continue
    if mode=='invalid':
        print('{"protocol":1,"protocol":1}',flush=True)
        continue
    result={'echo':request.get('payload'),'argv':sys.argv[2:]}
    if mode=='descendant':
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
        result['child_pid']=child.pid
    if mode=='inherited':
        fd,inode=int(sys.argv[2]),int(sys.argv[3])
        try: result['leaked']=os.fstat(fd).st_ino==inode
        except OSError: result['leaked']=False
    response=dict(protocol=1,request_id='wrong' if mode=='mismatch' else request['request_id'],
                  result=result,error=None,detail=None)
    sys.stdout.write(json.dumps(response)+ ('\r\n' if mode=='crlf' else '\n'))
    sys.stdout.flush()

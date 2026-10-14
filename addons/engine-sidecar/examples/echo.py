"""Offline protocol example. Logs belong on stderr; stdout is replies only."""
import json
import sys
for line in sys.stdin:
    if len(line)>4096:
        break
    request=json.loads(line)
    print(json.dumps(dict(protocol=1,request_id=request['request_id'],
        result=dict(echo=request.get('payload')),error=None,detail=None)),flush=True)

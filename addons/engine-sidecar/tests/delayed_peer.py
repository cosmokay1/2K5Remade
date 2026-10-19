"""Authored deadline fixture; no application, credentials or inference."""
import json
import sys
import time

for line in sys.stdin:
    request = json.loads(line)
    time.sleep(request['delay_ms'] / 1000)
    print(json.dumps(dict(protocol=1, request_id=request['request_id'],
                          result={'echo': request['payload']}, error=None,
                          detail=None)), flush=True)

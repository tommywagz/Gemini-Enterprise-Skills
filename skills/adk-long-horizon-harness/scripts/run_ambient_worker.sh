#!/usr/bin/env bash
# Local no-network Pub/Sub envelope mock; does not start FastAPI or ADK.
set -euo pipefail
[[ ${1:-} == --mock-event && -n ${2:-} ]] || { echo "usage: $0 --mock-event '{\"id\":\"e-1\"}'" >&2; exit 2; }
python3 - "$2" <<'PY'
import base64,json,sys
event=json.loads(sys.argv[1])
if not event.get('id'): raise SystemExit('mock event requires id')
data=base64.b64encode(json.dumps(event,separators=(',',':')).encode()).decode()
print(json.dumps({'message':{'messageId':'mock-'+event['id'],'data':data},'subscription':'mock-subscription'},indent=2))
PY

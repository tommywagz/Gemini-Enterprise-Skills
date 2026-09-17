#!/usr/bin/env python3
"""Validate a placeholder OAuth config and print a safe mock PKCE plan.

This tool cannot and does not register a Google OAuth client. It avoids live
secrets and network calls; production registration requires an authorized
administrator in the Google Cloud Console/API.
"""
import argparse,json,sys,urllib.parse
def main():
 p=argparse.ArgumentParser();p.add_argument('--mock',action='store_true');p.add_argument('--config',required=True);a=p.parse_args()
 if not a.mock: p.error('only --mock is supported; this helper never registers live clients')
 try: c=json.load(open(a.config))
 except Exception as e: print('config error: '+str(e),file=sys.stderr);return 2
 for k in ('client_id','redirect_uris','scopes'):
  if not c.get(k): print('config error: missing '+k,file=sys.stderr);return 2
 for u in c['redirect_uris']:
  x=urllib.parse.urlparse(u)
  if x.scheme not in ('https','http') or not x.netloc: print('config error: invalid redirect URI',file=sys.stderr);return 2
 print(json.dumps({'mode':'mock','pkce_required':True,'state_required':True,'nonce_required':True,'redirect_uris':c['redirect_uris'],'scopes':c['scopes']},indent=2));return 0
if __name__=='__main__':sys.exit(main())

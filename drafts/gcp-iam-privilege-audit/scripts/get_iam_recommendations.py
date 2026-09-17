#!/usr/bin/env python3
"""Read IAM Recommender recommendations or print a safe mock response.

Live mode makes one read-only REST GET using a bearer token read from stdin.
It never writes IAM policies or prints the token.
"""
import argparse,json,sys,urllib.parse,urllib.request
MOCK={"recommendations":[{"name":"projects/PROJECT/locations/global/recommenders/google.iam.policy.Recommender/recommendations/mock","stateInfo":{"state":"ACTIVE"},"primaryImpact":{"category":"SECURITY"},"content":{"operationGroups":[]},"description":"Mock: review broad IAM role against observed permissions."}]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--mock',action='store_true');p.add_argument('--token-stdin',action='store_true');a=p.parse_args()
 if a.mock: print(json.dumps(MOCK,indent=2).replace('PROJECT',a.project));return 0
 if not a.token_stdin: p.error('use --mock or --token-stdin')
 token=sys.stdin.read().strip()
 if not token: p.error('empty token on stdin')
 path='https://recommender.googleapis.com/v1/projects/'+urllib.parse.quote(a.project,safe='')+'/locations/global/recommenders/google.iam.policy.Recommender/recommendations'
 req=urllib.request.Request(path,headers={'Authorization':'Bearer '+token})
 try:
  with urllib.request.urlopen(req,timeout=20) as r: print(r.read().decode())
 except Exception as e: print('Recommender read failed: '+str(e),file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())

#!/usr/bin/env python3
"""Run a local JSON agent-evaluation dataset and write JUnit XML/Markdown.

No external dependencies. Dataset cases may supply `actual`, or `--command`
may supply it by reading the case prompt on stdin and writing one response on
stdout. Commands execute with shell=False.
"""
import argparse, html, json, re, subprocess, sys, time
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

def norm(s): return re.sub(r"\s+", " ", s.strip().casefold())
def overlap(a, b):
    a, b = set(re.findall(r"\w+", norm(a))), set(re.findall(r"\w+", norm(b)))
    return 1.0 if not a and not b else (0.0 if not a or not b else 2 * len(a & b) / (len(a) + len(b)))
def run_case(case, command, timeout):
    if "actual" in case: return case["actual"], None
    if not command: return None, "no actual output and no --command"
    try:
        p = subprocess.run(command, input=case["prompt"], text=True, capture_output=True, shell=False, timeout=timeout)
    except subprocess.TimeoutExpired: return None, f"command timed out after {timeout}s"
    if p.returncode: return None, f"command exited {p.returncode}: {p.stderr.strip()[:500]}"
    return p.stdout.strip(), None
def check(case, actual):
    fails=[]; expected=case["expected"]
    for x in case["assertions"]:
        t,v=x["type"],x.get("value")
        if t=="exact_match": ok=norm(actual)==norm(expected if v is None else str(v))
        elif t=="contains": ok=str(v) in actual
        elif t=="not_contains": ok=str(v) not in actual
        elif t=="route": ok=(norm(actual) in {"true","trigger","activate","yes"}) == bool(case.get("expected_route",v))
        elif t in {"min_token_overlap","min_semantic_similarity_proxy"}: ok=overlap(actual,expected)>=float(v)
        else: ok=False
        if not ok: fails.append(f"{t} failed" + (f" (value={v})" if v is not None else ""))
    return fails
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset",required=True); ap.add_argument("--command",nargs="+"); ap.add_argument("--timeout-seconds",type=float,default=30); ap.add_argument("--junit-out",required=True); ap.add_argument("--report-out",required=True); a=ap.parse_args()
    try: data=json.loads(Path(a.dataset).read_text())
    except Exception as e: print(f"dataset error: {e}",file=sys.stderr); return 2
    cases=data.get("cases",[])
    if not isinstance(cases,list) or not cases: print("dataset error: cases must be a non-empty list",file=sys.stderr); return 2
    suite=Element("testsuite",name="agent-evaluation",tests=str(len(cases))); results=[]; tp=fp=tn=fn=0
    for c in cases:
        node=SubElement(suite,"testcase",name=str(c.get("id","unnamed"))); started=time.time(); actual,err=run_case(c,a.command,a.timeout_seconds); node.set("time",f"{time.time()-started:.3f}")
        if err: SubElement(node,"error",message=err); results.append((c,"ERROR",err)); continue
        fails=check(c,actual)
        if any(x["type"]=="route" for x in c["assertions"]):
            want=bool(c.get("expected_route")); got=norm(actual) in {"true","trigger","activate","yes"}
            if want and got: tp+=1
            elif want: fn+=1
            elif got: fp+=1
            else: tn+=1
        if fails: SubElement(node,"failure",message="; ".join(fails)).text=actual[:2000]; results.append((c,"FAIL","; ".join(fails)))
        else: results.append((c,"PASS",""))
    errors=sum(r[1]=="ERROR" for r in results); failed=sum(r[1]=="FAIL" for r in results); suite.set("failures",str(failed)); suite.set("errors",str(errors)); ElementTree(suite).write(a.junit_out,encoding="utf-8",xml_declaration=True)
    rate=lambda n,d: "n/a" if not d else f"{n/d:.3f}"
    lines=["# Agent Evaluation Report","",f"- Dataset: `{a.dataset}`",f"- Cases: {len(cases)} | Passed: {len(cases)-failed-errors} | Failed: {failed} | Errors: {errors}",f"- Routing: TP={tp}, FP={fp}, TN={tn}, FN={fn}; precision={rate(tp,tp+fp)}, recall={rate(tp,tp+fn)}, FPR={rate(fp,fp+tn)}","","## Cases"]
    lines += [f"- `{c.get('id','unnamed')}`: **{s}** {m}" for c,s,m in results]
    Path(a.report_out).write_text("\n".join(lines)+"\n")
    print(f"cases={len(cases)} passed={len(cases)-failed-errors} failed={failed} errors={errors}")
    return 1 if failed or errors else 0
if __name__ == "__main__": sys.exit(main())

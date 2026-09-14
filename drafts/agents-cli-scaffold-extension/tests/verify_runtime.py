#!/usr/bin/env python3
"""Integration check for an already generated/installed/built workspace.

Usage: python3 tests/verify_runtime.py /absolute/generated/workspace
Starts only owned child processes; runs real ADK in demo mode, never a model.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

OPENER = build_opener(ProxyHandler({}))


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def request(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with OPENER.open(req, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        return exc.code, json.load(exc)


def ready(process, url):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError('server exited before readiness')
        try:
            if request(url)[0] == 200:
                return
        except (URLError, OSError):
            pass
        time.sleep(0.2)
    raise RuntimeError('server not ready after 20 seconds')


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main():
    root = Path(sys.argv[1]).resolve()
    adk_port, web_port = port(), port()
    while web_port == adk_port:
        web_port = port()
    base = f'http://127.0.0.1:{web_port}'
    env = {**os.environ, 'WORKSPACE_DEMO': '1', 'PORT': str(web_port),
           'ADK_BASE_URL': f'http://127.0.0.1:{adk_port}', 'OTEL_SDK_DISABLED': 'true'}
    processes = []
    with tempfile.TemporaryFile(mode='w+') as log:
        try:
            adk = subprocess.Popen([str(root / '.venv/bin/adk'), 'api_server',
                                    '--host', '127.0.0.1', '--port', str(adk_port), 'apps/agents'],
                                   cwd=root, env=env, stdout=log, stderr=log)
            processes.append(adk)
            ready(adk, env['ADK_BASE_URL'] + '/list-apps')
            web = subprocess.Popen(['node', 'apps/web/dist/index.js'], cwd=root,
                                   env=env, stdout=log, stderr=log)
            processes.append(web)
            ready(web, base + '/health')
            first = request(base + '/api/message', {'text': 'Hello polyglot'})
            assert first[0] == 200, first
            assert first[1]['text'] == 'DEMO: Hello polyglot', first
            second = request(base + '/api/message', {'text': 'second request'})
            assert second[0] == 200, second
            assert first[1]['sessionId'] != second[1]['sessionId']
            assert second[1]['text'] == 'DEMO: second request', second
            for invalid in ({}, {'text': ' '}, {'text': 7}, {'text': 'x', 'userId': 'other'}):
                assert request(base + '/api/message', invalid)[0] == 400
            stop(adk)
            assert request(base + '/api/message', {'text': 'offline'})[0] == 502
            print('PASS: real Hono -> ADK two-stage demo, isolated sessions, invalid inputs, upstream outage')
        except BaseException:
            log.seek(0)
            print(log.read(), file=sys.stderr)
            raise
        finally:
            for process in reversed(processes):
                stop(process)


if __name__ == '__main__':
    main()

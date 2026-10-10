"""Disposable public fixtures and loopback server for the browser test suite."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.support.paths import ROOT
from tests.support.publication import (
    add_approved_campaign_set,
    add_approved_notebook_set,
    add_proposal_release,
    create_sources,
    write_locks,
)
from tools.site_assembly import assemble_site


def build_fixtures(output: Path) -> None:
    os.environ['SOURCE_DATE_EPOCH'] = '1785628800'
    os.environ['GIT_CONFIG_NOSYSTEM'] = '1'
    os.environ['GIT_CONFIG_GLOBAL'] = os.devnull
    for name in tuple(os.environ):
        if name.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) or name in {
            'GIT_CONFIG_COUNT', 'GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
            'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL', 'GIT_DIR',
            'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_PARAMETERS',
        }:
            os.environ.pop(name)
    subprocess.run([sys.executable, '-m', 'mkdocs', 'build', '--strict', '--site-dir', str(output/'scaffold')], cwd=ROOT, check=True)
    sources=output/'sources';sources.mkdir()
    eu,py,commits=create_sources(sources)
    commits['euvics']=add_proposal_release(eu)
    add_approved_notebook_set(py, "print('Browser fixture notebook')\n")
    manifest_path=py/'publication/public-content-v1.json'
    notebooks=json.loads(manifest_path.read_text(encoding='utf-8'))['candidate_sets']
    add_approved_campaign_set(py)
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['candidate_sets'].extend(notebooks)
    manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
    subprocess.run(['git','add','.'],cwd=py,check=True)
    subprocess.run(['git','commit','-qm','Combine public synthetic browser fixtures'],cwd=py,check=True)
    commits['pyeuvics']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=py,text=True).strip()
    lock=write_locks(sources/'sources.lock.yml',commits)
    assemble_site(ROOT,lock,eu,py,output/'assembled')


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        # Match Pages' custom 404 body without pretending to test hosted access.
        prefix='assembled/site' if self.path.startswith('/assembled/site/') else 'scaffold'
        page=Path(self.directory)/prefix/'404.html'
        if code==404 and page.is_file():
            body=page.read_bytes()
            self.send_response(404)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().send_error(code,message,explain)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    def interrupted(signum: int, frame: object) -> None:
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    with TemporaryDirectory(prefix='euvics-browser-') as name:
        output=Path(name)
        build_fixtures(output)
        with ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(output))) as server:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__=='__main__':
    main()

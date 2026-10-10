"""Bounded external document tool and TeX/font package version evidence."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
from tools.privacy import PrivacyError,ScanProfile,scan_text
from .primitives import sha256_file

@dataclass(frozen=True)
class ToolVersion:
    name: str
    status: str
    version: str
    executable_sha256: str
    report_sha256: str

TOOLS=(('make',('--version',)),('latexmk',('-v',)),('pdflatex',('--version',)),('kpsewhich',('--version',)),('fc-list',('--version',)),('dpkg-query',('-W','-f=${Package} ${Version}\\n','texlive*','fonts-*')))


def capture_toolchain() -> tuple[ToolVersion,...]:
    records=[]
    for name,arguments in TOOLS:
        executable=shutil.which(name)
        if executable is None:
            records.append(ToolVersion(name,'unavailable','','',''));continue
        with tempfile.TemporaryFile() as output:
            try:
                result=subprocess.run([executable,*arguments],stdout=output,stderr=subprocess.STDOUT,timeout=15,check=False)
                if output.tell()>131072:raise ValueError('version report too large')
                output.seek(0);data=output.read();text=data.decode('utf-8')
                status='available' if result.returncode==0 else 'probe-failed'
                try:scan_text(text,'document tool version',ScanProfile.PUBLIC)
                except PrivacyError:text='Nonportable version text withheld; report fingerprint retained.'
                records.append(ToolVersion(name,status,text.strip(),sha256_file(Path(executable)),hashlib.sha256(data).hexdigest()))
            except (OSError,ValueError,subprocess.TimeoutExpired):
                records.append(ToolVersion(name,'probe-failed','','',''))
    return tuple(records)

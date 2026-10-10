"""Shared privacy vocabulary with explicit publication and runner profiles.

Heuristic rejection rules are not proof that arbitrary content is public.
No failure message includes a matched value or subprocess output.
"""
from __future__ import annotations

import codecs
import re
from enum import Enum
from pathlib import Path
from typing import BinaryIO


class PrivacyError(ValueError):
    """Content violates a named privacy rule or cannot be fully inspected."""


class ScanProfile(Enum):
    SOURCE = "source text"
    NOTEBOOK = "notebook output"
    PUBLIC = "generated public text"
    RUNNER = "runner residue"


PRIVATE_KEY = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED |DSA )?PRIVATE KEY-----")
LOCAL_PATH = re.compile(rb"(?:/Users/|/home/[^/\s]+/|\b[A-Za-z]:[\\/]+[A-Za-z0-9_.\x80-\xff-])")
CREDENTIALS = (
    PRIVATE_KEY,
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b"),
)
MAX_RECORD_BYTES = 1_048_576


def scan_bytes(payload: bytes, label: str, profile: ScanProfile) -> None:
    if profile is ScanProfile.RUNNER:
        if PRIVATE_KEY.search(payload):
            raise PrivacyError(f"private key material remains in runner temp: {label}")
        return
    if LOCAL_PATH.search(payload):
        raise PrivacyError(f"local absolute path detected in {label}")
    if any(pattern.search(payload) for pattern in CREDENTIALS):
        raise PrivacyError(f"credential-like material detected in {label}")


def scan_text(text: str, label: str, profile: ScanProfile) -> None:
    try:
        payload = text.encode("utf-8")
    except UnicodeError as exc:
        raise PrivacyError(f"invalid UTF-8 text in {label}") from exc
    scan_bytes(payload, label, profile)


def scan_stream(stream: BinaryIO, label: str, profile: ScanProfile, *, block_size: int = 65536) -> None:
    """Scan complete bounded records, retaining tokens across arbitrary block edges."""
    if block_size < 1:
        raise ValueError("scan block size must be positive")
    pending = b""
    decoder = codecs.getincrementaldecoder("utf-8")() if profile is not ScanProfile.RUNNER else None
    try:
        while block := stream.read(block_size):
            if decoder is not None:
                decoder.decode(block)
            parts = (pending + block).split(b"\n")
            for record in parts[:-1]:
                if len(record) > MAX_RECORD_BYTES:
                    raise PrivacyError(f"privacy scan record exceeds size limit: {label}")
                scan_bytes(record, label, profile)
            pending = parts[-1]
            if len(pending) > MAX_RECORD_BYTES:
                raise PrivacyError(f"privacy scan record exceeds size limit: {label}")
            scan_bytes(pending, label, profile)
        if decoder is not None:
            decoder.decode(b"", final=True)
    except (OSError, UnicodeError) as exc:
        raise PrivacyError(f"cannot inspect complete privacy input: {label}") from exc


def scan_file(path: Path, label: str, profile: ScanProfile) -> None:
    try:
        with path.open("rb") as stream:
            scan_stream(stream, label, profile)
    except OSError as exc:
        raise PrivacyError(f"cannot inspect privacy input: {label}") from exc

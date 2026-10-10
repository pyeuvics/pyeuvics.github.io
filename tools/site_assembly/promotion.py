"""Exclusive same-filesystem promotion of a fully verified directory.

Python's POSIX os.rename may replace an existing empty directory. Use native
no-replace operations instead; unsupported platforms fail closed. The workspace
is created beside the destination so normal builds stay on one filesystem.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys

from .primitives import FileOperationError


def promote_directory(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise FileOperationError('verified output must be an owned regular directory')
    if destination.exists() or destination.is_symlink():
        raise FileOperationError('output path already exists; refusing to replace it')
    try:
        if os.name == 'nt':
            # Windows rename fails if the destination exists, including a directory.
            os.rename(source, destination)
            return
        libc = ctypes.CDLL(None, use_errno=True)
        if sys.platform == 'darwin':
            rename = libc.renamex_np
            rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            # macOS SDK sys/stdio.h: RENAME_EXCL = 0x00000004.
            status = rename(os.fsencode(source), os.fsencode(destination), 4)
        elif sys.platform.startswith('linux'):
            rename = libc.renameat2
            rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            rename.restype = ctypes.c_int
            # AT_FDCWD = -100; RENAME_NOREPLACE = 1.
            status = rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
        else:
            raise FileOperationError('exclusive directory promotion is unsupported on this platform')
        if status != 0:
            number = ctypes.get_errno()
            raise OSError(number, os.strerror(number))
    except (AttributeError, OSError) as exc:
        raise FileOperationError('cannot exclusively promote verified output; existing paths are preserved') from exc

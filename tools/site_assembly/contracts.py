"""Compatibility facade for explicit, typed source-publication adapters."""
from pathlib import Path

from .contract_policy import COMMIT_RE as COMMIT_RE
from .contract_values import (ContractError as ContractError, _load_json as _load_json,
    _safe_path as _safe_path, _strict_object as _strict_object)
from .source_locks import load_locks as load_locks
from .source_checkout import (verify_checkout as verify_checkout,
    verify_contract_inputs as verify_contract_inputs, _validate_file)
from .contract_adapters.euvics import parse_euvics
from .contract_adapters.pyeuvics import parse_pyeuvics
from .models import SourceContract, SourceLock


def load_contract(lock: SourceLock, root: Path) -> SourceContract:
    """Decode once and dispatch only explicitly supported source adapters."""
    verify_checkout(lock, root)
    manifest = _load_json(root / lock.manifest_path)
    if lock.name == "euvics":
        files, notebooks = parse_euvics(manifest, lock, root)
    elif lock.name == "pyeuvics":
        files, notebooks = parse_pyeuvics(manifest, lock, root)
    else:
        raise ContractError(f"unsupported source name: {lock.name}")
    if len({item.path for item in files}) != len(files):
        raise ContractError(f"duplicate allowlist paths in {lock.name}")
    for item in files:
        _validate_file(root, item.path, lock.commit)
    return SourceContract(lock, root, tuple(sorted(files, key=lambda item: item.path)),
                          tuple(sorted(notebooks, key=lambda item: item.path)))

"""Tracked website input boundary, including the one canonical CSS alias."""
from __future__ import annotations

import stat
from pathlib import Path

from .primitives import run_text


class WebsiteInputError(ValueError):
    """The website tree contains unowned, missing or aliased publication inputs."""


CSS_ALIAS = 'content/stylesheets/readthedocs.css'
CSS_SOURCE = 'docs/stylesheets/readthedocs.css'
ROOT_INPUTS = ('mkdocs.yml', 'requirements-docs.txt', 'requirements-notebooks.txt', 'requirements-validation.txt', 'constraints-validation.txt', 'tools/dependency-policy.json', 'pyproject.toml', CSS_SOURCE)


def website_inputs(root: Path) -> tuple[str, ...]:
    names = tuple(sorted(filter(None, run_text(['git','ls-files','-z','--','content','overrides',*ROOT_INPUTS],root,'website input index').split('\0'))))
    required = {CSS_ALIAS, *ROOT_INPUTS}
    if not required.issubset(names):
        raise WebsiteInputError('required website inputs are not tracked')
    expected = {name for name in names if name.startswith(('content/', 'overrides/'))}
    actual: set[str] = set()
    for folder in ('content','overrides'):
        directory = root / folder
        if directory.is_symlink() or not directory.is_dir():
            raise WebsiteInputError('website input root is missing or aliased')
        for path in directory.rglob('*'):
            name = path.relative_to(root).as_posix()
            if path.is_symlink():
                if name != CSS_ALIAS or path.resolve(strict=True) != root / CSS_SOURCE:
                    raise WebsiteInputError(f'unapproved website symlink: {name}')
                actual.add(name)
            elif path.is_file():
                actual.add(name)
            elif not path.is_dir():
                raise WebsiteInputError(f'non-regular website input: {name}')
    if actual != expected:
        raise WebsiteInputError(f'website input ownership mismatch: extra={sorted(actual-expected)}, missing={sorted(expected-actual)}')
    for name in names:
        path = root / name
        if name == CSS_ALIAS:
            if not path.is_symlink():
                raise WebsiteInputError('canonical CSS input must retain its internal alias')
            continue
        current = path
        while current != root:
            if current.is_symlink():
                raise WebsiteInputError(f'unapproved website input alias: {name}')
            current = current.parent
        if not stat.S_ISREG(path.stat().st_mode):
            raise WebsiteInputError(f'website input is not regular: {name}')
    return names

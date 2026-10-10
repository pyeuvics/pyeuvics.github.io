from pathlib import Path

import pytest

from tools.site_assembly.pipeline import _scan_text, AssemblyError
from tools.site_assembly.notebooks import _scan, NotebookError
from tools.verify_runner_credentials import verify_no_private_keys, CredentialResidueError

BAD = [
    'ghp_'+'A'*35, 'github_pat_'+'A'*40, 'AKIA'+'A'*16,
    'eyJ'+'A'*25+'.'+'B'*25+'.'+'C'*15,
    '/Users/fixture/private', '/home/fixture/private',
    r'C:\Users\fixture\private', r'C:\\Users\\fixture\\private', 'C:/Users/fixture/private',
    '-----BEGIN PRIVATE KEY-----',
]


@pytest.mark.parametrize('scanner,error', [(_scan_text, AssemblyError), (_scan, NotebookError)])
@pytest.mark.parametrize('value', BAD)
def test_public_and_notebook_scans_share_rejection_vocabulary(scanner, error, value) -> None:
    with pytest.raises(error) as caught:
        scanner(value, 'synthetic fixture')
    assert value not in str(caught.value)


@pytest.mark.parametrize('scanner', [_scan_text, _scan])
def test_safe_urls_and_device_descriptions_remain_accepted(scanner) -> None:
    scanner('https://pyeuvics.github.io/ and device names (c:\\)', 'fixture')


def test_runner_keeps_key_only_profile(tmp_path: Path) -> None:
    (tmp_path/'ordinary').write_bytes(b'\xff\x00ghp_'+b'A'*35)
    verify_no_private_keys(tmp_path)


def test_runner_stream_boundaries_and_unreadable_files(tmp_path: Path, monkeypatch) -> None:
    path=tmp_path/'key'
    path.write_bytes(b'A'*65520+b'\n-----BEGIN OPENSSH PRIVATE KEY-----\nfixture')
    with pytest.raises(CredentialResidueError, match='private key material remains'):
        verify_no_private_keys(tmp_path)
    original=Path.open
    def deny(self,*args,**kwargs):
        if self==path:
            raise PermissionError('synthetic unreadable file')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',deny)
    with pytest.raises(CredentialResidueError,match='cannot inspect'):
        verify_no_private_keys(tmp_path)


@pytest.mark.parametrize('value', BAD)
def test_streamed_public_values_match_across_small_blocks(value) -> None:
    import io
    from tools.privacy import PrivacyError, ScanProfile, scan_stream
    with pytest.raises(PrivacyError):
        scan_stream(io.BytesIO(('prefix '+value).encode('utf-8')), 'fixture', ScanProfile.PUBLIC, block_size=3)


def test_public_stream_rejects_invalid_utf8_and_oversized_records() -> None:
    import io
    from tools.privacy import PrivacyError, ScanProfile, scan_stream, MAX_RECORD_BYTES
    for payload in [b'\xff', b'a'*(MAX_RECORD_BYTES+1)]:
        with pytest.raises(PrivacyError):
            scan_stream(io.BytesIO(payload), 'fixture', ScanProfile.PUBLIC)

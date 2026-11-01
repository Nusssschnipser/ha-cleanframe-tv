"""Fetch the exact SDK package used in the device tests; no SDK binary in Git."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

URL = 'https://download.tizen.org/sdk/tizenstudio/official/binary/sdb_4.2.35_ubuntu-64.zip'
SHA256 = 'dd07b2f28f1ebe27631017ebd993fdfd54f30b2262891ed40d2f890ac8309c03'

def main():
    with urllib.request.urlopen(URL, timeout=60) as response:
        archive = response.read(10_000_001)
    if len(archive) > 10_000_000 or hashlib.sha256(archive).hexdigest() != SHA256:
        raise RuntimeError('SDK archive checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        binary = package.read('data/tools/sdb')
    target = Path('/usr/local/bin/sdb')
    target.write_bytes(binary)
    target.chmod(0o755)

if __name__ == '__main__': main()

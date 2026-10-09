"""X・Threads で共通の HTTP 補助。"""
import json
import urllib.error
import urllib.request
import uuid

from errors import PostError


def http(req, label, timeout=60):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise PostError(f"{label} エラー {e.code}: {e.read().decode(errors='replace')}")


def multipart(fields, file_field, filename, data, ctype):
    boundary = "----ad" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(
        (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
         f"Content-Type: {ctype}\r\n\r\n").encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"

import base64
from hashlib import sha256


def encode_name(name: str) -> str:
    new_name = base64.b32encode(sha256(name.encode()).digest()).rstrip(b"=").decode().lower()
    if ord('0') <= ord(new_name[0]) <= ord('9'):  # The name shouldn't start with the number.
        new_name = chr(100) + new_name[1:]
    return new_name

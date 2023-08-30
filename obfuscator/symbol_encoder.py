import base64
import random
from hashlib import sha256


def encode_name(name: str) -> str:
    new_name = base64.b32encode(sha256(name.encode()).digest()).rstrip(b"=").decode().lower()
    if ord('0') <= ord(new_name[0]) <= ord('9'):
        new_name = f"z{new_name[1:]}"
        # new_name = chr(random.randint(97, 122)) + new_name[1:]
    return new_name

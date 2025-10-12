import hashlib
import hmac
import random
import secrets
import string
from datetime import datetime


def generate_deterministic_id(input_str):
    # Hash the input string using the SHA-256 algorithm
    hash_obj = hashlib.sha256(input_str.encode())
    # Get the hexadecimal representation of the hash
    hex_str = hash_obj.hexdigest()
    # Return the first 16 characters of the hexadecimal string as the ID
    return str(int(hex_str[:16], 16))


def generate_uid(length=6, prefix="") -> str:
    return prefix + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )


def generate_id(length=12, prefix="") -> str:
    lower_bound = 10 ** (length - 1)
    upper_bound = 10**length - 1
    return prefix + str(secrets.randbelow(upper_bound - lower_bound) + lower_bound)


def generate_token(length=64, prefix=""):
    return prefix + secrets.token_urlsafe(length)


def create_hmac(secret_key, message):
    message = message.encode("utf-8")
    secret_key = secret_key.encode("utf-8")

    # HMAC object requires a byte object. Hence, the secret_key and message are encoded to 'utf-8'
    signature = hmac.new(secret_key, message, digestmod=hashlib.sha256).hexdigest()
    return signature


def generate_and_sign_hmac(secret: str, user_id: str):
    timestamp = int(datetime.now().timestamp())
    nonce = generate_id(12)
    input_set = sorted(
        ["timestamp=" + str(timestamp), "nonce=" + nonce, "user_id=" + user_id]
    )
    return {
        "nonce": nonce,
        "signature": create_hmac(secret, "&".join(input_set)),
        "timestamp": timestamp,
        "user_id": user_id,
    }

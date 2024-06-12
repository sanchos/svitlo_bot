import hashlib
import hmac
import json
import time

import requests

from auth import get_access_token
from config import settings


def get_timestamp():
    return str(int(time.time() * 1000))


def generate_sign_str(query_params, body, method, headers, base_path):
    sorted_params = sorted(query_params.items())
    url = "&".join([f"{key}={value}" for key, value in sorted_params])
    if url:
        url = "/" + base_path + "?" + url
    else:
        url = "/" + base_path

    body_str = json.dumps(body) if body else ""
    sha256 = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

    headers_str = ""
    if "Signature-Headers" in headers:
        sign_header_keys = headers["Signature-Headers"].split(":")
        for key in sign_header_keys:
            headers_str += f"{key}:{headers.get(key, '')}\n"

    sign_url = f"{method.upper()}\n{sha256}\n{headers_str}\n{url}"
    return sign_url


def calc_sign(client_id, access_token, timestamp, nonce, sign_str, secret):
    message = (client_id + access_token + timestamp + nonce + sign_str).encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    signature = hmac.new(secret_bytes, message, hashlib.sha256).hexdigest().upper()
    return signature


def get_device_status(device_id: str = settings.DEVICE_ID):
    base_path = "v1.0/devices"
    url = f"{settings.BASE_URL}/{base_path}/{device_id}"
    access_token = (
        get_access_token()
    )  # Assuming you have a function that retrieves a valid access token
    timestamp = get_timestamp()
    nonce = ""
    headers = {
        "client_id": settings.CLIENT_ID,
        "sign_method": "HMAC-SHA256",
        "t": timestamp,
        "access_token": access_token,
        "nonce": nonce,
    }

    sign_str = generate_sign_str({}, None, "GET", headers, f"{base_path}/{device_id}")
    signature = calc_sign(
        settings.CLIENT_ID, access_token, timestamp, nonce, sign_str, settings.SECRET
    )
    headers["sign"] = signature

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    result = response.json()["result"]["online"]
    return result


if __name__ == "__main__":
    print(get_device_status())

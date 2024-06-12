import hashlib
import hmac
import json
import time

import requests

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


def calc_sign(client_id, timestamp, nonce, sign_str, secret):
    message = (client_id + timestamp + nonce + sign_str).encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    signature = hmac.new(secret_bytes, message, hashlib.sha256).hexdigest().upper()
    return signature


def get_access_token() -> str:
    client_id = settings.CLIENT_ID
    secret = settings.SECRET

    # URL and query parameters
    base_path = "v1.0/token"
    url = f"{settings.BASE_URL}/{base_path}"
    params = {"grant_type": "1"}

    # Generate timestamp and nonce
    timestamp = get_timestamp()
    nonce = ""  # If there is a nonce value, add it here

    # Prepare headers
    headers = {
        "client_id": client_id,
        "sign_method": "HMAC-SHA256",
        # Include any other headers you need
    }

    # Generate the sign string
    sign_str = generate_sign_str(params, None, "GET", headers, base_path)

    # Generate the signature
    signature = calc_sign(client_id, timestamp, nonce, sign_str, secret)

    # Add the signature and timestamp to headers
    headers.update(
        {
            "sign": signature,
            "t": timestamp,
        }
    )

    # Make the GET request
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for HTTP errors
    token = response.json().get("result", {}).get("access_token")

    return token


if __name__ == "__main__":
    print(get_access_token())

"""X (Twitter) API v2 ile görselli gönderi.

Gerekenler (X Developer Console → uygulamanız → "Keys and tokens";
uygulama izni "Read and write" olmalı):
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET

Ücret: X API kullandıkça öde modelindedir; bağlantısız bir gönderi ~0,015 $.
Bu kod bilinçli olarak bağlantı eklemez (bağlantılı gönderi ~0,20 $).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
import urllib.parse as up
from pathlib import Path

import requests

API = "https://api.x.com/2"


def _q(s: str) -> str:
    return up.quote(str(s), safe="~-._")


def _oauth1_baslik(yontem: str, url: str) -> str:
    """OAuth 1.0a HMAC-SHA1 imzası (gövde parametreleri imzaya girmez: JSON/multipart)."""
    p = {
        "oauth_consumer_key": os.environ["X_API_KEY"],
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": os.environ["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    parametre = "&".join(f"{_q(k)}={_q(v)}" for k, v in sorted(p.items()))
    taban = "&".join([yontem.upper(), _q(url), _q(parametre)])
    anahtar = f"{_q(os.environ['X_API_SECRET'])}&{_q(os.environ['X_ACCESS_SECRET'])}"
    p["oauth_signature"] = base64.b64encode(
        hmac.new(anahtar.encode(), taban.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_q(k)}="{_q(v)}"' for k, v in sorted(p.items()))


def _medya_yukle(gorsel: Path) -> str:
    url = f"{API}/media/upload"
    with open(gorsel, "rb") as f:
        r = requests.post(url, headers={"Authorization": _oauth1_baslik("POST", url)},
                          files={"media": (gorsel.name, f, "image/jpeg")},
                          data={"media_category": "tweet_image", "media_type": "image/jpeg"},
                          timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"X medya yükleme başarısız ({r.status_code}): {r.text}")
    j = r.json()
    return str(j.get("data", {}).get("id") or j.get("media_id_string") or j.get("media_id"))


def paylas(gorsel: Path, metin: str) -> str:
    medya_id = _medya_yukle(gorsel)
    url = f"{API}/tweets"
    r = requests.post(url, headers={"Authorization": _oauth1_baslik("POST", url)},
                      json={"text": metin, "media": {"media_ids": [medya_id]}}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"X gönderi başarısız ({r.status_code}): {r.text}")
    return r.json()["data"]["id"]

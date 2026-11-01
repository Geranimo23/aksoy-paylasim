"""Instagram Graph API ile tek görselli gönderi paylaşımı.

Gerekenler (ortam değişkenleri):
  IG_USER_ID       Instagram profesyonel hesabının ID'si
  IG_ACCESS_TOKEN  instagram_content_publish izinli erişim anahtarı
  IG_API_HOST      (isteğe bağlı) graph.facebook.com  |  graph.instagram.com
  IG_API_VERSION   (isteğe bağlı) v23.0
"""
from __future__ import annotations

import os
import time

import requests


def paylas(gorsel_url: str, aciklama: str) -> str:
    host = os.getenv("IG_API_HOST", "graph.facebook.com")
    surum = os.getenv("IG_API_VERSION", "v23.0")
    kullanici = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    taban = f"https://{host}/{surum}"

    # 1) Medya kabı oluştur — Instagram görseli bu adresten indirir
    r = requests.post(f"{taban}/{kullanici}/media",
                      data={"image_url": gorsel_url, "caption": aciklama, "access_token": token},
                      timeout=60)
    _kontrol(r, "medya kabı")
    kap = r.json()["id"]

    # 2) Kap hazır olana kadar bekle
    for _ in range(20):
        s = requests.get(f"{taban}/{kap}", params={"fields": "status_code", "access_token": token}, timeout=30)
        _kontrol(s, "durum sorgusu")
        durum = s.json().get("status_code")
        if durum == "FINISHED":
            break
        if durum in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram medya kabı hatası: {s.json()}")
        time.sleep(3)

    # 3) Yayınla
    p = requests.post(f"{taban}/{kullanici}/media_publish",
                      data={"creation_id": kap, "access_token": token}, timeout=60)
    _kontrol(p, "yayınlama")
    return p.json()["id"]


def _kontrol(r: requests.Response, adim: str) -> None:
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram {adim} başarısız ({r.status_code}): {r.text}")

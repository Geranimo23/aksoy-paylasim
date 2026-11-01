"""LinkedIn Posts API ile görselli gönderi (şirket sayfası veya kişisel profil).

Gerekenler:
  LINKEDIN_ACCESS_TOKEN  w_organization_social (sayfa) veya w_member_social (profil) izinli
  LINKEDIN_AUTHOR_URN    urn:li:organization:12345678   veya   urn:li:person:AbCdEf
  LINKEDIN_API_VERSION   (isteğe bağlı) YYYYMM, ör. 202606
"""
from __future__ import annotations

import os
import time
import urllib.parse as up
from pathlib import Path

import requests

API = "https://api.linkedin.com/rest"


def _basliklar() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['LINKEDIN_ACCESS_TOKEN']}",
        "LinkedIn-Version": os.getenv("LINKEDIN_API_VERSION", "202606"),
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _kontrol(r: requests.Response, adim: str) -> None:
    if r.status_code >= 400:
        raise RuntimeError(f"LinkedIn {adim} başarısız ({r.status_code}): {r.text}")


def paylas(gorsel: Path, metin: str, alt_metin: str) -> str:
    yazar = os.environ["LINKEDIN_AUTHOR_URN"]

    # 1) Görsel yükleme alanı aç
    r = requests.post(f"{API}/images?action=initializeUpload", headers=_basliklar(),
                      json={"initializeUploadRequest": {"owner": yazar}}, timeout=60)
    _kontrol(r, "görsel başlatma")
    deger = r.json()["value"]
    yukleme_url, gorsel_urn = deger["uploadUrl"], deger["image"]

    # 2) Görseli yükle
    with open(gorsel, "rb") as f:
        u = requests.put(yukleme_url, data=f.read(), timeout=120,
                         headers={"Authorization": _basliklar()["Authorization"]})
    _kontrol(u, "görsel yükleme")

    # 3) Görsel işlenene kadar bekle
    for _ in range(20):
        s = requests.get(f"{API}/images/{up.quote(gorsel_urn, safe='')}", headers=_basliklar(), timeout=30)
        if s.ok and s.json().get("status") == "AVAILABLE":
            break
        time.sleep(3)

    # 4) Gönderiyi oluştur
    govde = {
        "author": yazar,
        "commentary": metin,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                         "thirdPartyDistributionChannels": []},
        "content": {"media": {"id": gorsel_urn, "altText": alt_metin[:4086]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    p = requests.post(f"{API}/posts", headers=_basliklar(), json=govde, timeout=60)
    _kontrol(p, "gönderi")
    return p.headers.get("x-restli-id", "tamam")

"""Her platform için gönderi metnini hazırlar."""
from __future__ import annotations

import re
import unicodedata

UYARI = "Bu paylaşım bilgilendirme amaçlıdır; hukuki danışmanlık niteliği taşımaz."


def _hashtagler(karar: dict, ayar: dict, en_fazla: int | None = None) -> list[str]:
    h = ayar.get("hashtagler", {})
    liste = list(h.get("genel", [])) + list(h.get(karar.get("konu", ""), [])) + list(karar.get("etiketler", []) or [])
    goruldu, sonuc = set(), []
    for t in liste:
        t = t if t.startswith("#") else f"#{t}"
        if t.lower() not in goruldu:
            goruldu.add(t.lower())
            sonuc.append(t)
    return sonuc[:en_fazla] if en_fazla else sonuc


def kunye(karar: dict) -> str:
    return (f"Yargıtay {karar.get('daire', '')}, E. {karar.get('esas', '-')}, "
            f"K. {karar.get('karar', '-')}, T. {karar.get('tarih', '-')}")


def instagram(karar: dict, ayar: dict) -> str:
    parcalar = [f"⚖️ {karar['baslik']}", karar.get("ozet", "").strip()]
    if karar.get("alinti"):
        parcalar.append(f"📌 “{karar['alinti'].strip()}”")
    parcalar += [f"📚 {kunye(karar)}", f"ℹ️ {UYARI}", " ".join(_hashtagler(karar, ayar, 30))]
    return "\n\n".join(p for p in parcalar if p)[:2200]


# ---- X (Twitter) ----------------------------------------------------------
def _x_uzunluk(s: str) -> int:
    """X'in ağırlıklı karakter sayımına yakın hesap (emoji/CJK = 2)."""
    n = 0
    for c in s:
        if ord(c) > 0xFFFF or unicodedata.east_asian_width(c) in ("W", "F"):
            n += 2
        else:
            n += 1
    return n


def x(karar: dict, ayar: dict) -> str:
    """280 karaktere sığdırır. Bağlantı EKLEMEZ (X, bağlantılı gönderiye ~13 kat ücret alır)."""
    bas = f"⚖️ {karar['baslik']}"
    daire = karar.get("daire", "").replace("Hukuk Dairesi", "HD").replace("Ceza Dairesi", "CD")
    kun = f"📚 Yargıtay {daire} E.{karar.get('esas', '')} K.{karar.get('karar', '')}"
    etiketler = _hashtagler(karar, ayar)
    etiket = " ".join([etiketler[0]] + [t for t in etiketler[1:] if t in
                                          ayar.get("hashtagler", {}).get(karar.get("konu", ""), [])][:1])
    ozet = re.sub(r"\s+", " ", karar.get("ozet", "")).strip()

    def kur(o):
        return "\n\n".join(p for p in [bas, o, kun, etiket] if p)

    metin = kur(ozet)
    if _x_uzunluk(metin) <= 280:
        return metin
    # Önce tam cümleleri koru
    cumleler = re.split(r"(?<=[.!?])\s+", ozet)
    for n in range(len(cumleler) - 1, 0, -1):
        aday = kur(" ".join(cumleler[:n]))
        if _x_uzunluk(aday) <= 280:
            return aday
    # Tek cümle bile sığmıyorsa kelime kelime kısalt
    kelimeler = ozet.split()
    while kelimeler and _x_uzunluk(kur(" ".join(kelimeler) + "…")) > 280:
        kelimeler.pop()
    metin = kur(" ".join(kelimeler) + "…" if kelimeler else "")
    if _x_uzunluk(metin) > 280:  # başlık bile çok uzunsa
        metin = "\n\n".join([bas, kun])[:280]
    return metin


# ---- LinkedIn -------------------------------------------------------------
_LI_OZEL = r"\|{}@[]()<>#*_~"


def _li_kacis(s: str) -> str:
    """LinkedIn 'little text' biçiminde ayrılmış karakterleri kaçışlar."""
    return "".join("\\" + c if c in _LI_OZEL else c for c in s)


def linkedin(karar: dict, ayar: dict) -> str:
    parcalar = [
        f"⚖️ {karar['baslik']}",
        karar.get("ozet", "").strip(),
    ]
    if karar.get("alinti"):
        parcalar.append(f"Kararda öne çıkan tespit: “{karar['alinti'].strip()}”")
    parcalar += [kunye(karar), UYARI]
    govde = "\n\n".join(_li_kacis(p) for p in parcalar if p)
    etiketler = " ".join("{hashtag|\\#|" + t.lstrip("#") + "}" for t in _hashtagler(karar, ayar, 8))
    return f"{govde}\n\n{etiketler}"

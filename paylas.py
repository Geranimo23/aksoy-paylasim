#!/usr/bin/env python3
"""Aksoy Hukuk Bürosu — sıradaki onaylı Yargıtay kararını Instagram, X ve LinkedIn'de paylaşır.

Kullanım:
  python paylas.py                 # sıradaki onaylı kararı paylaş
  python paylas.py --onizleme      # paylaşmadan görsel + metinleri onizleme/ klasörüne üret
  python paylas.py --kuyruk        # kuyruğun durumunu listele
  python paylas.py --dosya 003-x.yaml --platform x   # belirli dosya / platform
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import time
from pathlib import Path

import requests
import yaml

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))

from src import gorsel, metin  # noqa: E402
from src.platformlar import barindirma, instagram, linkedin, x  # noqa: E402

KUYRUK = KOK / "kararlar"
ARSIV = KUYRUK / "paylasilanlar"
GECMIS = KOK / "gecmis.json"
ZORUNLU = ["daire", "esas", "karar", "tarih", "konu", "baslik", "ozet"]


def yukle_ayar() -> dict:
    return yaml.safe_load((KOK / "config.yaml").read_text(encoding="utf-8"))


def yukle_gecmis() -> dict:
    return json.loads(GECMIS.read_text(encoding="utf-8")) if GECMIS.exists() else {}


def kaydet_gecmis(g: dict) -> None:
    GECMIS.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")


def etkin_platformlar(ayar: dict, secim: str | None) -> list[str]:
    p = [k for k, v in ayar["platformlar"].items() if v]
    return [secim] if secim else p


def dogrula(karar: dict, dosya: Path) -> None:
    eksik = [a for a in ZORUNLU if not str(karar.get(a, "")).strip()]
    if eksik:
        raise SystemExit(f"✗ {dosya.name}: eksik alan(lar): {', '.join(eksik)}")


def siradaki(ayar: dict, gecmis: dict, platformlar: list[str]) -> Path | None:
    for f in sorted(KUYRUK.glob("*.yaml")):
        k = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if ayar.get("onay_zorunlu", True) and k.get("onay") is not True:
            continue
        yapilan = gecmis.get(f.name, {}).get("platformlar", {})
        if any(p not in yapilan for p in platformlar):
            return f
    return None


def kuyruk_listele(ayar: dict, gecmis: dict) -> None:
    dosyalar = sorted(KUYRUK.glob("*.yaml"))
    onayli = 0
    print(f"{'DOSYA':45} {'ONAY':6} DURUM")
    for f in dosyalar:
        k = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        ok = k.get("onay") is True
        onayli += ok
        yapilan = ", ".join(gecmis.get(f.name, {}).get("platformlar", {})) or "-"
        print(f"{f.name:45} {'evet' if ok else 'HAYIR':6} {yapilan}")
    print(f"\nToplam {len(dosyalar)} karar, {onayli} onaylı. "
          f"Haftada 4 paylaşımla yaklaşık {onayli / 4:.1f} haftalık onaylı içerik var.")


def herkese_acik_url(yol: Path, ayar: dict) -> str:
    if ayar.get("gorsel_barindirma") == "imgbb":
        return barindirma.imgbb(yol)
    url = barindirma.github(yol, KOK)
    for _ in range(10):  # raw adresin yayına girmesini bekle
        if requests.head(url, timeout=15).status_code == 200:
            break
        time.sleep(3)
    return url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--onizleme", action="store_true")
    ap.add_argument("--kuyruk", action="store_true")
    ap.add_argument("--dosya")
    ap.add_argument("--platform", choices=["instagram", "x", "linkedin"])
    a = ap.parse_args()

    ayar, gecmis = yukle_ayar(), yukle_gecmis()
    if a.kuyruk:
        kuyruk_listele(ayar, gecmis)
        return 0

    platformlar = etkin_platformlar(ayar, a.platform)

    if a.dosya:
        dosya = KUYRUK / a.dosya
        if not dosya.exists():
            raise SystemExit(f"✗ Bulunamadı: {dosya}")
    else:
        dosya = siradaki(ayar, gecmis, platformlar)
        if dosya is None:
            if a.onizleme and (ilk := sorted(KUYRUK.glob("*.yaml"))):
                dosya = ilk[0]  # önizlemede onay şartı aranmaz
            else:
                print("✗ Kuyrukta paylaşılacak ONAYLI karar kalmadı. kararlar/ klasörüne yeni karar ekleyin.")
                return 1  # GitHub size e-posta ile haber verir

    karar = yaml.safe_load(dosya.read_text(encoding="utf-8"))
    dogrula(karar, dosya)
    print(f"→ {dosya.name}: {karar['baslik']}")

    metinler = {"instagram": metin.instagram(karar, ayar),
                "x": metin.x(karar, ayar),
                "linkedin": metin.linkedin(karar, ayar)}

    if a.onizleme:
        klasor = KOK / "onizleme"
        yol = gorsel.kart_olustur(karar, ayar, klasor / f"{dosya.stem}.jpg")
        for p, m in metinler.items():
            (klasor / f"{dosya.stem}-{p}.txt").write_text(m, encoding="utf-8")
        print(f"✓ Önizleme hazır: {klasor}  (görsel: {yol.name})")
        print(f"  X metni {metin._x_uzunluk(metinler['x'])}/280 karakter")
        return 0

    bugun = dt.date.today().isoformat()
    yol = gorsel.kart_olustur(karar, ayar, KOK / "public" / f"{bugun}-{dosya.stem}.jpg")
    kayit = gecmis.setdefault(dosya.name, {"baslik": karar["baslik"], "platformlar": {}})
    hatalar = []

    for p in platformlar:
        if p in kayit["platformlar"]:
            print(f"  · {p}: daha önce paylaşılmış, atlanıyor")
            continue
        try:
            if p == "instagram":
                kimlik = instagram.paylas(herkese_acik_url(yol, ayar), metinler["instagram"])
            elif p == "x":
                kimlik = x.paylas(yol, metinler["x"])
            else:
                kimlik = linkedin.paylas(yol, metinler["linkedin"], f"{karar['baslik']}. {karar['ozet']}")
            kayit["platformlar"][p] = {"id": kimlik, "tarih": dt.datetime.now().isoformat(timespec="minutes")}
            print(f"  ✓ {p}: {kimlik}")
        except Exception as e:  # bir platformun hatası diğerlerini durdurmasın
            hatalar.append(f"{p}: {e}")
            print(f"  ✗ {p}: {e}")
        kaydet_gecmis(gecmis)

    if all(p in kayit["platformlar"] for p in etkin_platformlar(ayar, None)):
        ARSIV.mkdir(exist_ok=True)
        shutil.move(str(dosya), ARSIV / dosya.name)
        print(f"✓ {dosya.name} arşive taşındı")

    if hatalar:
        print("\nHatalı platformlar bir sonraki çalışmada yeniden denenecek:\n  " + "\n  ".join(hatalar))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

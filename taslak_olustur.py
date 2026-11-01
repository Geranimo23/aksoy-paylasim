#!/usr/bin/env python3
"""İSTEĞE BAĞLI: ham/ klasöründeki karar metinlerinden (.txt) Claude ile paylaşım taslağı üretir.

Yargıtay karar arama sitesinden (karararama.yargitay.gov.tr) kararın tam metnini kopyalayıp
ham/ klasörüne .txt olarak kaydedin, sonra:

  ANTHROPIC_API_KEY=... python taslak_olustur.py

Her metin için kararlar/ klasörüne `onay: false` olan bir YAML taslağı yazılır.
Taslağı okuyup düzelttikten sonra `onay: true` yapmanız gerekir — yapay zekâ özetleri
hata içerebilir; yayın öncesi avukat kontrolü şarttır.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
import yaml

KOK = Path(__file__).resolve().parent
HAM, KUYRUK = KOK / "ham", KOK / "kararlar"
ISLENEN = HAM / "islenenler"

ISTEM = """Aşağıda bir Yargıtay kararının tam metni var. Bir hukuk bürosunun sosyal medya
hesabında paylaşılacak bilgilendirici bir gönderi için SADECE şu JSON'u döndür:

{"daire": "...", "esas": "YYYY/NNNN", "karar": "YYYY/NNNN", "tarih": "GG.AA.YYYY",
 "konu": "is|ticaret|gayrimenkul|aile|miras|icra|borclar|ceza",
 "baslik": "8-12 kelimelik, kararın ilkesini anlatan başlık",
 "ozet": "2-3 cümle, sade Türkçe, kararın verdiği hukuki ilke",
 "alinti": "karar metninden AYNEN alınmış, en fazla 30 kelimelik can alıcı cümle",
 "etiketler": ["#...", "#..."]}

Kurallar: Daire, esas, karar numarası ve tarihi yalnızca metinden al; metinde yoksa boş bırak,
asla tahmin etme. Alıntı metinde birebir geçmeli. Reklam niteliğinde ifade ("en iyi", "bize
ulaşın" vb.) kullanma. Taraf isimlerine yer verme.

KARAR METNİ:
"""


def _slug(s: str) -> str:
    tablo = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"[^a-z0-9]+", "-", s.translate(tablo).lower()).strip("-")[:40]


def _sonraki_no() -> int:
    nolar = [int(m.group(1)) for f in list(KUYRUK.glob("*.yaml")) + list((KUYRUK / "paylasilanlar").glob("*.yaml"))
             if (m := re.match(r"(\d+)-", f.name))]
    return max(nolar, default=0) + 1


def taslak(metin_: str) -> dict:
    ayar = yaml.safe_load((KOK / "config.yaml").read_text(encoding="utf-8"))
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": ayar.get("ai", {}).get("model", "claude-sonnet-5-5"), "max_tokens": 1500,
              "messages": [{"role": "user", "content": ISTEM + metin_[:150_000]}]},
        timeout=180,
    )
    r.raise_for_status()
    yanit = "".join(b.get("text", "") for b in r.json()["content"])
    return json.loads(yanit[yanit.find("{"): yanit.rfind("}") + 1])


def main() -> int:
    dosyalar = sorted(HAM.glob("*.txt"))
    if not dosyalar:
        print("ham/ klasöründe .txt karar metni yok.")
        return 0
    ISLENEN.mkdir(exist_ok=True)
    for f in dosyalar:
        try:
            k = taslak(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"✗ {f.name}: {e}")
            continue
        k["onay"] = False
        hedef = KUYRUK / f"{_sonraki_no():03d}-{_slug(k.get('baslik', f.stem))}.yaml"
        hedef.write_text("# YAPAY ZEKÂ TASLAĞI — kontrol edip onay: true yapın\n" +
                         yaml.safe_dump(k, allow_unicode=True, sort_keys=False, width=88), encoding="utf-8")
        f.rename(ISLENEN / f.name)
        print(f"✓ {f.name} → {hedef.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

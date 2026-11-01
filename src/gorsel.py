"""Karar bilgisinden 1080x1350 (Instagram 4:5) paylaşım kartı üretir."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parent.parent
FONT = KOK / "fontlar"

W, H = 1080, 1350
KENAR = 96  # metin kenar boşluğu

KONU_ADLARI = {
    "is": "İŞ HUKUKU",
    "ticaret": "TİCARET HUKUKU",
    "gayrimenkul": "GAYRİMENKUL HUKUKU",
    "aile": "AİLE HUKUKU",
    "miras": "MİRAS HUKUKU",
    "icra": "İCRA VE İFLAS HUKUKU",
    "borclar": "BORÇLAR HUKUKU",
    "ceza": "CEZA HUKUKU",
}


def _font(ad: str, boyut: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT / ad), boyut)


def _upper_tr(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def _sar(metin: str, font, genislik: int, draw: ImageDraw.ImageDraw) -> list[str]:
    satirlar, mevcut = [], ""
    for kelime in metin.split():
        deneme = f"{mevcut} {kelime}".strip()
        if draw.textlength(deneme, font=font) <= genislik:
            mevcut = deneme
        else:
            if mevcut:
                satirlar.append(mevcut)
            mevcut = kelime
    if mevcut:
        satirlar.append(mevcut)
    return satirlar


def _aralikli(draw, xy, metin, font, renk, aralik):
    """Harf aralıklı (letter-spacing) yazı; ortalı."""
    toplam = sum(draw.textlength(c, font=font) for c in metin) + aralik * (len(metin) - 1)
    x = xy[0] - toplam / 2
    for c in metin:
        draw.text((x, xy[1]), c, font=font, fill=renk)
        x += draw.textlength(c, font=font) + aralik


def _terazi(draw, cx, cy, renk, olcek=1.0):
    """Basit adalet terazisi simgesi."""
    s = olcek
    draw.line([(cx, cy - 34 * s), (cx, cy + 30 * s)], fill=renk, width=int(3 * s))
    draw.ellipse([cx - 5 * s, cy - 42 * s, cx + 5 * s, cy - 32 * s], fill=renk)
    draw.line([(cx - 46 * s, cy - 24 * s), (cx + 46 * s, cy - 24 * s)], fill=renk, width=int(3 * s))
    draw.line([(cx - 20 * s, cy + 32 * s), (cx + 20 * s, cy + 32 * s)], fill=renk, width=int(4 * s))
    for yon in (-1, 1):
        x = cx + yon * 46 * s
        draw.line([(x, cy - 24 * s), (x - 16 * s, cy + 4 * s)], fill=renk, width=int(2 * s))
        draw.line([(x, cy - 24 * s), (x + 16 * s, cy + 4 * s)], fill=renk, width=int(2 * s))
        draw.chord([x - 20 * s, cy - 12 * s, x + 20 * s, cy + 16 * s], 0, 180, fill=renk)


def kart_olustur(karar: dict, ayar: dict, cikti: Path) -> Path:
    r = ayar["renkler"]
    img = Image.new("RGB", (W, H), r["zemin"])
    d = ImageDraw.Draw(img)

    # Hafif dikey geçiş
    z1 = tuple(int(r["zemin"][i:i + 2], 16) for i in (1, 3, 5))
    z2 = tuple(int(r["zemin_ikinci"][i:i + 2], 16) for i in (1, 3, 5))
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(z1[k] + (z2[k] - z1[k]) * t) for k in range(3)))

    # Çift altın çerçeve
    d.rectangle([36, 36, W - 36, H - 36], outline=r["altin"], width=3)
    d.rectangle([48, 48, W - 48, H - 48], outline=r["altin"], width=1)

    # Üst kısım: terazi + büro adı
    _terazi(d, W // 2, 140, r["altin"], 1.0)
    _aralikli(d, (W // 2, 200), ayar["buro"]["ad"], _font("DejaVuSerif-Bold.ttf", 34), r["altin"], 6)
    _aralikli(d, (W // 2, 250), _upper_tr(ayar["buro"]["alt_baslik"]), _font("DejaVuSans.ttf", 20),
              r["metin_soluk"], 8)

    # Konu etiketi
    konu = KONU_ADLARI.get(karar.get("konu", ""), _upper_tr(karar.get("konu", "")))
    if konu:
        f = _font("DejaVuSans-Bold.ttf", 20)
        gw = d.textlength(konu, font=f) + 48
        x0 = (W - gw) / 2
        d.rounded_rectangle([x0, 306, x0 + gw, 346], radius=20, outline=r["altin"], width=2)
        d.text((W / 2, 326), konu, font=f, fill=r["altin_acik"], anchor="mm")

    alt_sinir = H - 230  # alt bilgi alanından önce
    genislik = W - 2 * KENAR

    # Başlık + özet + alıntı alanı sığana kadar küçült
    for olcek in [1.0, 0.94, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58]:
        fb = _font("DejaVuSerif-Bold.ttf", int(60 * olcek))
        fo = _font("DejaVuSans.ttf", int(32 * olcek))
        fa = _font("DejaVuSerif-Italic.ttf", int(30 * olcek))
        b_s = _sar(karar["baslik"], fb, genislik, d)
        o_s = _sar(karar.get("ozet", ""), fo, genislik, d)
        a_s = _sar(karar.get("alinti", "") or "", fa, genislik - 50, d)
        lb, lo, la = int(fb.size * 1.22), int(fo.size * 1.45), int(fa.size * 1.45)
        yukseklik = len(b_s) * lb + 50 + len(o_s) * lo + ((60 + len(a_s) * la) if a_s else 0)
        if 390 + yukseklik <= alt_sinir:
            break
    else:
        a_s = []  # hâlâ sığmıyorsa alıntıyı düşür

    y = 390
    for s in b_s:
        d.text((W / 2, y), s, font=fb, fill=r["metin"], anchor="ma")
        y += lb
    y += 18
    d.line([(W / 2 - 60, y), (W / 2 + 60, y)], fill=r["altin"], width=3)
    y += 32
    for s in o_s:
        d.text((KENAR, y), s, font=fo, fill=r["metin"])
        y += lo
    if a_s:
        y += 30
        d.line([(KENAR, y), (KENAR, y + len(a_s) * la)], fill=r["altin"], width=4)
        for s in a_s:
            d.text((KENAR + 30, y), s, font=fa, fill=r["altin_acik"])
            y += la

    # Alt bilgi: daire, esas/karar, tarih
    d.line([(KENAR, H - 200), (W - KENAR, H - 200)], fill=r["altin"], width=1)
    kunye1 = f"Yargıtay {karar.get('daire', '')}".strip()
    kunye2 = f"E. {karar.get('esas', '-')}  ·  K. {karar.get('karar', '-')}  ·  T. {karar.get('tarih', '-')}"
    d.text((W / 2, H - 176), kunye1, font=_font("DejaVuSerif-Bold.ttf", 28), fill=r["altin"], anchor="ma")
    d.text((W / 2, H - 134), kunye2, font=_font("DejaVuSans.ttf", 24), fill=r["metin_soluk"], anchor="ma")
    if ayar["buro"].get("imza"):
        d.text((W / 2, H - 96), ayar["buro"]["imza"], font=_font("DejaVuSans.ttf", 20),
               fill=r["metin_soluk"], anchor="ma")

    cikti.parent.mkdir(parents=True, exist_ok=True)
    img.save(cikti, "JPEG", quality=92)  # Instagram JPEG ister
    return cikti

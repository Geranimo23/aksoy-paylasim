"""Instagram'ın görseli çekebilmesi için herkese açık adres üretir."""
from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path

import requests


def github(gorsel: Path, kok: Path) -> str:
    """Görseli depoya commit+push eder; raw.githubusercontent.com adresi döner (depo public olmalı)."""
    depo = os.environ["GITHUB_REPOSITORY"]          # Actions otomatik verir: kullanici/depo
    dal = os.getenv("GITHUB_REF_NAME", "main")
    goreli = gorsel.relative_to(kok).as_posix()
    calis = lambda *a: subprocess.run(a, cwd=kok, check=True)
    calis("git", "config", "user.name", "paylasim-botu")
    calis("git", "config", "user.email", "paylasim-botu@users.noreply.github.com")
    calis("git", "add", goreli)
    calis("git", "commit", "-m", f"Görsel: {gorsel.name}")
    calis("git", "push")
    return f"https://raw.githubusercontent.com/{depo}/{dal}/{goreli}"


def imgbb(gorsel: Path) -> str:
    r = requests.post("https://api.imgbb.com/1/upload",
                      data={"key": os.environ["IMGBB_API_KEY"],
                            "image": base64.b64encode(gorsel.read_bytes()).decode()},
                      timeout=120)
    r.raise_for_status()
    return r.json()["data"]["url"]

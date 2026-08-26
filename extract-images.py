#!/usr/bin/env python3
"""
Витягує всі зображення з презентації Google Slides, збереженої як .pptx.

Як користуватись
----------------
1. У Google Slides: Файл → Завантажити → Microsoft PowerPoint (.pptx)
2. Покладіть завантажений файл поруч із цим скриптом
3. python3 extract-images.py shpargalka.pptx

Скрипт покладе всі картинки в assets/raw/ з іменами вигляду
slide03-img1.png — тобто одразу видно, з якого слайда кожне фото.
Далі перейменуйте потрібні у фінальні імена (див. нижче) і покладіть
в assets/.

Фінальні імена, які очікує index.html:
    assets/hurghada.jpg       — слайд 3  (Хургада)
    assets/sharm.jpg          — слайд 4  (Шарм-ель-Шейх)
    assets/marsa-alam.jpg     — слайд 5  (Марса-Алам)
    assets/akka.jpg           — слайд 6  (готелі Akka)
    assets/crm-leads.png      — слайд 7  (індивідуальні запити в CRM)
    assets/passport-scan.png  — слайд 8  (сканування паспортів)
    assets/premium.jpg        — слайд 14 (Travelon Premium 24/7)

Якщо файлу немає — секція просто покаже фірмовий градієнт замість фото,
нічого не зламається.
"""

import os
import re
import shutil
import sys
import zipfile
from collections import defaultdict

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "raw")


def slide_number(rels_name: str) -> str:
    m = re.search(r"slide(\d+)\.xml\.rels$", rels_name)
    return m.group(1).zfill(2) if m else "00"


def main(path: str) -> None:
    if not zipfile.is_zipfile(path):
        sys.exit(f"Це не .pptx: {path}")

    os.makedirs(OUT, exist_ok=True)

    with zipfile.ZipFile(path) as z:
        names = z.namelist()

        # media -> список слайдів, де воно використовується
        usage = defaultdict(list)
        for rels in [n for n in names if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", n)]:
            xml = z.read(rels).decode("utf-8", "ignore")
            for target in re.findall(r'Target="\.\./media/([^"]+)"', xml):
                usage[target].append(slide_number(rels))

        media = sorted(n for n in names if n.startswith("ppt/media/"))
        if not media:
            sys.exit("У файлі немає вбудованих зображень.")

        counter = defaultdict(int)
        saved = 0
        for m in media:
            base = os.path.basename(m)
            ext = os.path.splitext(base)[1].lower()
            if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".emf", ".wmf"}:
                continue

            slides = usage.get(base) or ["xx"]
            for s in slides:
                counter[s] += 1
                out_name = f"slide{s}-img{counter[s]}{ext}"
                with z.open(m) as src, open(os.path.join(OUT, out_name), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                saved += 1
                print(f"  slide {s}  →  assets/raw/{out_name}")

    print(f"\nГотово: {saved} файл(ів) у {OUT}")
    print("Перейменуйте потрібні згідно зі списком у шапці скрипта та покладіть у assets/")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Використання: python3 extract-images.py <файл.pptx>")
    main(sys.argv[1])

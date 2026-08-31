# -*- coding: utf-8 -*-
"""
Генератор синтетических сканов документов для демо ИИ-агента 1С:ЗУП.

Три «скана» на человека:
  - паспорт РФ, разворот страниц 2-3 (вертикальный, как в жизни);
  - свидетельство ИНН, форма № 2-1-Учет;
  - страховое свидетельство ОПС — зелёная карточка со СНИЛС.

Из них агент извлекает реквизиты и заводит физлицо и сотрудника в ЗУП.

Вёрстка повторяет расположение полей настоящих бланков — в этом смысл демо:
агент читает реальную структуру документа. Сами документы намеренно нерабочие:

  - серия паспорта 99 XX, такие серии не выдаются;
  - регион ИНН 99, такого кода региона нет;
  - эмитенты вида «ТЕСТОВОЕ ОВД ДЕМОНСТРАЦИОННОГО ОКРУГА»;
  - вместо герба — абстрактная розетка, госсимволику не рисуем;
  - в печатях по центру написано «ОБРАЗЕЦ»;
  - водяной знак «ОБРАЗЕЦ» и красная строка «НЕ ЯВЛЯЕТСЯ ДОКУМЕНТОМ» на листе.

Контрольные разряды ИНН и СНИЛС считаются по-настоящему: 1С проверяет их
прямо в поле ввода и мусор не примет.

Запуск:  python generate_scans.py [--count N] [--seed N] [--out КАТАЛОГ]
"""

import argparse
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS = "C:/Windows/Fonts"
F_REG = os.path.join(FONTS, "arial.ttf")
F_BOLD = os.path.join(FONTS, "arialbd.ttf")
F_SERIF = os.path.join(FONTS, "times.ttf")
F_SERIF_BOLD = os.path.join(FONTS, "timesbd.ttf")
F_SERIF_IT = os.path.join(FONTS, "timesi.ttf")
F_MONO = os.path.join(FONTS, "cour.ttf")
F_MONO_BOLD = os.path.join(FONTS, "courbd.ttf")

INK = (48, 46, 48)
INK_SOFT = (108, 100, 100)

PASSPORT_PAPER = (243, 233, 230)
PASSPORT_GUILLOCHE = (231, 206, 205)
PASSPORT_RED = (176, 54, 58)
PASSPORT_LABEL = (150, 92, 92)

INN_PAPER = (250, 243, 239)
INN_GUILLOCHE = (235, 214, 210)
INN_ORNAMENT = (186, 148, 146)
INN_STAMP = (106, 74, 140)
HOLOGRAM = (188, 164, 108)

SNILS_PAPER = (226, 236, 216)
SNILS_BAND = (158, 184, 146)
SNILS_GUILLOCHE = (198, 216, 188)
SNILS_INK = (44, 54, 44)

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]

TRANSLIT = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E",
    "Ж": "ZH", "З": "Z", "И": "I", "Й": "I", "К": "K", "Л": "L", "М": "M",
    "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
    "Ф": "F", "Х": "KH", "Ц": "TS", "Ч": "CH", "Ш": "SH", "Щ": "SHCH",
    "Ъ": "IE", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "IU", "Я": "IA", "-": "<",
}

PEOPLE = [
    dict(surname="Астахова", name="Мария", patronymic="Игоревна",
         sex="ЖЕН.", birth="14.03.1991", birthplace="ГОР. ВОРОНЕЖ"),
    dict(surname="Бельский", name="Артём", patronymic="Николаевич",
         sex="МУЖ.", birth="02.11.1985", birthplace="ГОР. КАЗАНЬ"),
    dict(surname="Гвоздева", name="Ольга", patronymic="Петровна",
         sex="ЖЕН.", birth="27.06.1978", birthplace="ПОС. ЛУГОВОЙ ТЮМЕНСКОЙ ОБЛ."),
    dict(surname="Дорохов", name="Сергей", patronymic="Владимирович",
         sex="МУЖ.", birth="09.09.1996", birthplace="ГОР. НОВОСИБИРСК"),
    dict(surname="Ерёмина", name="Анна", patronymic="Дмитриевна",
         sex="ЖЕН.", birth="21.01.1988", birthplace="ГОР. РОСТОВ-НА-ДОНУ"),
    dict(surname="Жиляев", name="Константин", patronymic="Андреевич",
         sex="МУЖ.", birth="05.05.1982", birthplace="ГОР. ПЕРМЬ"),
    dict(surname="Зотова", name="Полина", patronymic="Сергеевна",
         sex="ЖЕН.", birth="18.07.1993", birthplace="ГОР. САМАРА"),
    dict(surname="Ильченко", name="Роман", patronymic="Валерьевич",
         sex="МУЖ.", birth="30.12.1979", birthplace="С. КРАСНЫЙ ЯР ОМСКОЙ ОБЛ."),
    dict(surname="Кабанова", name="Вера", patronymic="Аркадьевна",
         sex="ЖЕН.", birth="03.04.1986", birthplace="ГОР. ЯРОСЛАВЛЬ"),
    dict(surname="Луговой", name="Денис", patronymic="Олегович",
         sex="МУЖ.", birth="25.08.1990", birthplace="ПГТ. ЗАРЕЧНЫЙ СВЕРДЛОВСКОЙ ОБЛ."),
    dict(surname="Мещерякова", name="Алина", patronymic="Тимуровна",
         sex="ЖЕН.", birth="11.02.1998", birthplace="ГОР. УФА РЕСПУБЛИКИ БАШКОРТОСТАН"),
    dict(surname="Нечаев", name="Игорь", patronymic="Станиславович",
         sex="МУЖ.", birth="07.10.1975", birthplace="ГОР. ВОЛГОГРАД"),
    dict(surname="Осипова", name="Дарья", patronymic="Максимовна",
         sex="ЖЕН.", birth="22.05.1995", birthplace="ГОР. КАЛИНИНГРАД"),
    dict(surname="Пантелеев", name="Юрий", patronymic="Борисович",
         sex="МУЖ.", birth="16.01.1983", birthplace="Д. МАЛЫЕ ГОРКИ ТВЕРСКОЙ ОБЛ."),
    dict(surname="Рогова", name="Светлана", patronymic="Львовна",
         sex="ЖЕН.", birth="29.09.1981", birthplace="ГОР. ИРКУТСК"),
    dict(surname="Савельев", name="Никита", patronymic="Григорьевич",
         sex="МУЖ.", birth="12.06.2000", birthplace="ГОР. ТУЛА"),
    dict(surname="Тарасова", name="Екатерина", patronymic="Ивановна",
         sex="ЖЕН.", birth="04.11.1987", birthplace="ГОР. ХАБАРОВСК"),
    dict(surname="Ушаков", name="Павел", patronymic="Викторович",
         sex="МУЖ.", birth="19.03.1992", birthplace="СТ. ЛЕНИНГРАДСКАЯ КРАСНОДАРСКОГО КРАЯ"),
    dict(surname="Фомина", name="Людмила", patronymic="Егоровна",
         sex="ЖЕН.", birth="08.08.1976", birthplace="ГОР. САРАТОВ"),
    dict(surname="Хромов", name="Артур", patronymic="Русланович",
         sex="МУЖ.", birth="26.02.1999", birthplace="ГОР. ГРОЗНЫЙ ЧЕЧЕНСКОЙ РЕСПУБЛИКИ"),
]

ISSUERS = [
    "ТЕСТОВЫМ ТУ МВД РОССИИ ПО ЦЕНТРАЛЬНОМУ РАЙОНУ ГОР. ДЕМОНСТРАЦИОННЫЙ",
    "ТЕСТОВЫМ ОТДЕЛОМ УФМС РОССИИ ПО УЧЕБНОЙ ОБЛАСТИ В ГОР. ПРИМЕРНЫЙ",
    "ТЕСТОВЫМ ОВД ДЕМОНСТРАЦИОННОГО ОКРУГА УЧЕБНОГО КРАЯ",
]

TAX_OFFICES = [
    "ТЕСТОВАЯ ИНСПЕКЦИЯ ФНС РОССИИ № 9900",
    "ТЕСТОВАЯ МЕЖРАЙОННАЯ ИФНС РОССИИ № 9901",
]


# ───────────────────────── реквизиты ─────────────────────────

def make_inn(rnd):
    """12-значный ИНН физлица с настоящими контрольными разрядами. Регион 99."""
    d = [9, 9] + [rnd.randint(0, 9) for _ in range(8)]
    w11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    n11 = sum(a * b for a, b in zip(d, w11)) % 11 % 10
    d11 = d + [n11]
    w12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    n12 = sum(a * b for a, b in zip(d11, w12)) % 11 % 10
    return "".join(map(str, d11 + [n12]))


def make_snils(rnd):
    """СНИЛС с настоящей контрольной суммой, формат XXX-XXX-XXX YY."""
    while True:
        d = [rnd.randint(0, 9) for _ in range(9)]
        if int("".join(map(str, d))) <= 1001998:
            continue
        s = sum(x * (9 - i) for i, x in enumerate(d))
        if s < 100:
            k = s
        elif s in (100, 101):
            k = 0
        else:
            k = s % 101
            if k in (100, 101):
                k = 0
        n = "".join(map(str, d))
        return "%s-%s-%s %02d" % (n[0:3], n[3:6], n[6:9], k)


def make_person(i, rnd):
    p = dict(PEOPLE[i % len(PEOPLE)])
    p["inn"] = make_inn(rnd)
    p["snils"] = make_snils(rnd)
    p["passport_series"] = "99 %02d" % rnd.randint(1, 20)
    p["passport_number"] = "%06d" % rnd.randint(100000, 999999)
    p["issued_by"] = rnd.choice(ISSUERS)
    year = int(p["birth"].split(".")[-1]) + rnd.choice([20, 21, 22])
    p["issued_at"] = "%02d.%02d.%d" % (rnd.randint(1, 28), rnd.randint(1, 12), year)
    p["dept_code"] = "%03d-%03d" % (rnd.randint(700, 799), rnd.randint(1, 99))
    p["snils_registered_at"] = "%02d.%02d.%d" % (
        rnd.randint(1, 28), rnd.randint(1, 12), year + 1)
    p["tax_office"] = rnd.choice(TAX_OFFICES)
    p["inn_blank"] = "99 № %07d" % rnd.randint(1000000, 9999999)
    p["fio"] = "%s %s %s" % (p["surname"], p["name"], p["patronymic"])
    return p


def words_date(ddmmyyyy, upper=False, with_goda=False):
    """01.02.1990 → «1 февраля 1990» (или «1 ФЕВРАЛЯ 1990»)."""
    d, m, y = ddmmyyyy.split(".")
    s = "%d %s %s" % (int(d), MONTHS[int(m) - 1], y)
    if with_goda:
        s += " года"
    return s.upper() if upper else s


def translit(s):
    return "".join(TRANSLIT.get(ch, ch) for ch in s.upper())


# ───────────────────────── примитивы ─────────────────────────

def font(path, size):
    return ImageFont.truetype(path, size)


def paper(w, h, rnd, tint):
    img = Image.new("RGB", (w, h), tint)
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 700)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(-5, 5)
        d.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in tint))
    return img


def guilloche(img, color, amp=8, step=12, phase=0.0, box=None):
    d = ImageDraw.Draw(img)
    w, h = img.size
    x0, y0b, x1, y1b = box if box else (0, 0, w, h)
    for y0 in range(int(y0b) - amp, int(y1b) + amp, step):
        pts = []
        for x in range(int(x0), int(x1) + 8, 8):
            y = y0 + amp * math.sin(x / 44.0 + phase + y0 / 88.0)
            if y0b <= y <= y1b:
                pts.append((x, y))
        if len(pts) > 1:
            d.line(pts, fill=color, width=1)


def rosette(img, cx, cy, r, color, petals=30):
    """Абстрактный защитный узор. Госсимволику не рисуем."""
    d = ImageDraw.Draw(img)
    for k in range(petals):
        a = 2 * math.pi * k / petals
        dx, dy = math.cos(a) * r * 0.34, math.sin(a) * r * 0.34
        d.ellipse([cx - r * 0.62 + dx, cy - r * 0.62 + dy,
                   cx + r * 0.62 + dx, cy + r * 0.62 + dy], outline=color)


def tile_text(img, text, f, color, dx, dy, angle=0):
    w, h = img.size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, h * 2, dy):
        off = 0 if (y // dy) % 2 == 0 else dx // 2
        for x in range(-dx, w * 2, dx):
            d.text((x + off, y), text, font=f, fill=color)
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, center=(w // 2, h // 2))
    return Image.alpha_composite(img.convert("RGBA"),
                                 layer.crop((0, 0, w, h))).convert("RGB")


def spaced(d, xy, text, f, fill, extra=6, center_w=None):
    """Текст с разрядкой — как «Р О С С И Й С К А Я  Ф Е Д Е Р А Ц И Я»."""
    total = sum(d.textlength(c, font=f) + extra for c in text) - extra
    x, y = xy
    if center_w:
        x = (center_w - total) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + extra
    return total


def ctext(d, y, text, f, fill, width):
    d.text(((width - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def perforated(text, f, color, dot=2, grid=4):
    """Текст «пробитый» точками — перфорация серии и номера паспорта."""
    tmp = Image.new("L", (2400, 220), 0)
    ImageDraw.Draw(tmp).text((20, 20), text, font=f, fill=255)
    tmp = tmp.crop(tmp.getbbox())
    w, h = tmp.size
    out = Image.new("RGBA", (w + grid * 2, h + grid * 2), (0, 0, 0, 0))
    do = ImageDraw.Draw(out)
    px = tmp.load()
    for y in range(0, h, grid):
        for x in range(0, w, grid):
            if px[x, y] > 120:
                cx, cy = x + grid, y + grid
                do.ellipse([cx - dot, cy - dot, cx + dot, cy + dot],
                           fill=color + (255,))
    return out


def squiggle(d, x, y, w, rnd, color=(46, 46, 92), width=3, amp=1.0):
    pts = []
    n = 30
    for i in range(n):
        t = i / (n - 1.0)
        pts.append((x + w * t,
                    y - amp * (17 * math.sin(t * 7.2 + rnd.random())
                               + 12 * math.sin(t * 2.3))))
    d.line(pts, fill=color, width=width, joint="curve")


def round_stamp(img, cx, cy, r, arc_text, mid_lines, color, rnd, width=4):
    """Круглая печать: текст по дуге, розетка внутри, «ОБРАЗЕЦ» по центру."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color + (170,)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=width)
    d.ellipse([cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86],
              outline=c, width=2)
    d.ellipse([cx - r * 0.52, cy - r * 0.52, cx + r * 0.52, cy + r * 0.52],
              outline=c, width=1)

    fa = font(F_BOLD, int(r * 0.15))
    n = len(arc_text)
    for i, ch in enumerate(arc_text):
        a = -math.pi / 2 + (i - (n - 1) / 2.0) * (2 * math.pi / (n * 1.35))
        ch_img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
        ImageDraw.Draw(ch_img).text((12, 8), ch, font=fa, fill=c)
        ch_img = ch_img.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        layer.alpha_composite(
            ch_img, (int(cx + math.cos(a) * r * 0.7) - 20,
                     int(cy + math.sin(a) * r * 0.7) - 20))

    d = ImageDraw.Draw(layer)
    fm = font(F_BOLD, int(r * 0.16))
    for i, s in enumerate(mid_lines):
        tw = d.textlength(s, font=fm)
        d.text((cx - tw / 2, cy - r * 0.18 + i * r * 0.22), s, font=fm, fill=c)

    layer = layer.rotate(rnd.uniform(-8, 8), resample=Image.BICUBIC, center=(cx, cy))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for word in words:
        probe = (cur + " " + word).strip()
        if d.textlength(probe, font=f) > width:
            lines.append(cur)
            cur = word
        else:
            cur = probe
    lines.append(cur)
    return lines


def rule(d, x1, y, x2, color=(170, 160, 158), width=1):
    d.line([(x1, y), (x2, y)], fill=color, width=width)


def watermark(img, rnd, size_div=13):
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(F_BOLD, int(w / size_div))
    for k in range(0, 4):
        d.text((int(w * 0.06), int(h * (0.12 + 0.24 * k))), "ОБРАЗЕЦ",
               font=f, fill=(130, 130, 140, 34))
    layer = layer.rotate(28, resample=Image.BICUBIC, center=(w // 2, h // 2))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

    d = ImageDraw.Draw(img)
    f2 = font(F_REG, max(11, int(w / 74)))
    msg = "СИНТЕТИЧЕСКИЙ ОБРАЗЕЦ · НЕ ЯВЛЯЕТСЯ ДОКУМЕНТОМ · ДАННЫЕ ВЫМЫШЛЕНЫ"
    d.text(((w - d.textlength(msg, font=f2)) / 2, h - int(w / 26)), msg,
           font=f2, fill=(168, 88, 88))
    return img


def scanify(img, rnd, fill=(252, 250, 247)):
    img = img.rotate(rnd.uniform(-0.7, 0.7), resample=Image.BICUBIC,
                     expand=True, fillcolor=fill)
    img = img.filter(ImageFilter.GaussianBlur(0.45))
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h / 240)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        v = rnd.randint(-13, 13)
        r, g, b = px[x, y]
        px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)),
                    max(0, min(255, b + v)))
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(18):
        a = int(12 - i * 0.65)
        if a <= 0:
            break
        d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=(0, 0, 0, a))
    return img


# ───────────────────────── паспорт ─────────────────────────

def photo_frame(d, x, y, w, h, color):
    """Орнаментальная красная рамка вокруг фотографии."""
    d.rectangle([x, y, x + w, y + h], outline=color, width=2)
    d.rectangle([x + 7, y + 7, x + w - 7, y + h - 7], outline=color, width=1)
    step = 15
    for i in range(x + 7, x + w - 7, step):
        d.arc([i, y - 2, i + step, y + 14], 180, 360, fill=color)
        d.arc([i, y + h - 14, i + step, y + 2 + h], 0, 180, fill=color)
    for j in range(y + 7, y + h - 7, step):
        d.arc([x - 2, j, x + 14, j + step], 90, 270, fill=color)
        d.arc([x + w - 14, j, x + w + 2, j + step], 270, 90, fill=color)


def draw_passport(p, rnd):
    W, H = 1490, 2090                       # вертикальный разворот 2-3
    MID = 1010                              # линия перфорации между страницами
    img = paper(W, H, rnd, PASSPORT_PAPER)
    guilloche(img, PASSPORT_GUILLOCHE, amp=7, step=11, phase=0.0)
    guilloche(img, (236, 216, 214), amp=4, step=15, phase=1.9)
    for cx, cy in ((360, 700), (1120, 1560)):
        rosette(img, cx, cy, 210, (238, 220, 218))
    img = tile_text(img, "RUSSIA", font(F_BOLD, 22),
                    (232, 212, 210, 150), 250, 118, angle=0)

    d = ImageDraw.Draw(img)
    f_lbl = font(F_SERIF, 25)
    f_val = font(F_SERIF_BOLD, 37)
    f_val_s = font(F_SERIF_BOLD, 30)

    # ══ страница 2 ══
    spaced(d, (0, 78), "РОССИЙСКАЯ ФЕДЕРАЦИЯ", font(F_SERIF_BOLD, 33),
           (86, 74, 74), extra=11, center_w=W)

    d.text((92, 190), "Паспорт выдан", font=f_lbl, fill=INK_SOFT)
    lines = wrap(d, p["issued_by"], f_val_s, 1000)
    yy = 178
    for i in range(3):
        rule(d, 300 if i == 0 else 92, yy + 44, W - 92, (182, 158, 156))
        if i < len(lines):
            d.text((312 if i == 0 else 104, yy + 4), lines[i],
                   font=f_val_s, fill=INK)
        yy += 62

    y = 400
    d.text((92, y + 8), "Дата выдачи", font=f_lbl, fill=INK_SOFT)
    d.text((300, y), p["issued_at"], font=f_val, fill=INK)
    rule(d, 290, y + 46, 640, (182, 158, 156))
    d.text((690, y + 8), "Код подразделения", font=f_lbl, fill=INK_SOFT)
    d.text((1010, y), p["dept_code"], font=f_val, fill=INK)
    rule(d, 1000, y + 46, W - 92, (182, 158, 156))

    d.text((1010, 640), "Личный код", font=f_lbl, fill=INK_SOFT)
    rule(d, 1000, 632, W - 92, (182, 158, 156))
    d.text((1010, 790), "Личная подпись", font=f_lbl, fill=INK_SOFT)
    rule(d, 1000, 782, W - 92, (182, 158, 156))
    squiggle(d, 1030, 772, 300, rnd, color=(52, 48, 84), width=3)
    squiggle(d, 200, 700, 240, rnd, color=(52, 48, 84), width=3, amp=0.8)

    rosette(img, W // 2 - 40, 700, 74, (222, 168, 168))
    img = round_stamp(img, W // 2 - 40, 700, 175,
                      "ТЕСТОВОЕ ПОДРАЗДЕЛЕНИЕ", ["ОБРАЗЕЦ", p["dept_code"]],
                      PASSPORT_RED, rnd)
    d = ImageDraw.Draw(img)
    d.text((W // 2 - 70, 800), "М. П.", font=font(F_SERIF, 22), fill=PASSPORT_RED)

    # ══ перфорационная полоса ══
    for x in range(60, W - 60, 26):
        d.rectangle([x, MID - 26, x + 15, MID + 4], fill=(206, 96, 92))
        d.rectangle([x + 4, MID - 20, x + 11, MID - 2], fill=(232, 168, 164))

    # ══ страница 3 ══
    px_, py_, pw, ph = 96, MID + 120, 330, 424
    photo_frame(d, px_, py_, pw, ph, PASSPORT_RED)
    for i in range(1, 6):
        rule(d, px_ + 16, py_ + ph * i / 6, px_ + pw - 16, (226, 206, 204))
    ff = font(F_SERIF, 26)
    d.text((px_ + (pw - d.textlength("ФОТОГРАФИЯ", font=ff)) / 2, py_ + ph / 2 - 16),
           "ФОТОГРАФИЯ", font=ff, fill=(206, 178, 176))

    rosette(img, W - 150, MID + 120, 62, (196, 150, 172))
    d = ImageDraw.Draw(img)

    xl, xv = 480, 700
    y = MID + 100
    for label, value in (("Фамилия", p["surname"].upper()),
                         ("Имя", p["name"].upper()),
                         ("Отчество", p["patronymic"].upper())):
        d.text((xl, y + 12), label, font=font(F_SERIF, 24), fill=PASSPORT_LABEL)
        d.text((xv, y), value, font=f_val, fill=INK)
        rule(d, xl, y + 52, W - 96, (198, 172, 170))
        y += 84

    d.text((xl, y + 12), "Пол", font=font(F_SERIF, 24), fill=PASSPORT_LABEL)
    d.text((xv - 130, y), p["sex"], font=f_val, fill=INK)
    d.text((xv + 20, y + 4), "Дата\nрождения", font=font(F_SERIF, 21),
           fill=PASSPORT_LABEL)
    d.text((xv + 200, y), p["birth"], font=f_val, fill=INK)
    rule(d, xl, y + 62, W - 96, (198, 172, 170))
    y += 96

    d.text((xl, y + 4), "Место\nрождения", font=font(F_SERIF, 21),
           fill=PASSPORT_LABEL)
    yy = y
    for line in wrap(d, p["birthplace"], f_val_s, W - xv - 110):
        d.text((xv, yy), line, font=f_val_s, fill=INK)
        yy += 40
    rule(d, xl, y + 62, W - 96, (198, 172, 170))

    # ══ машиночитаемая зона ══
    mrz_y = H - 210
    d.rectangle([0, mrz_y - 26, W, H - 96], fill=(247, 241, 232))
    fam = translit(p["surname"])
    nm = translit(p["name"])
    pat = translit(p["patronymic"])
    l1 = ("PNRUS" + fam + "<<" + nm + "<" + pat).ljust(44, "<")[:44]
    ser = p["passport_series"].replace(" ", "")
    bd = p["birth"].split(".")
    sx = "M" if p["sex"].startswith("М") else "F"
    l2 = (ser + p["passport_number"] + "<RUS" + bd[2][2:] + bd[1] + bd[0]
          + sx + "<<<<<<<<<<<<<<<" + ser + "<" + p["dept_code"].replace("-", ""))
    l2 = l2.ljust(44, "<")[:44]
    fz = font(F_MONO_BOLD, 30)
    for i, ln in enumerate((l1, l2)):
        d.text((58, mrz_y + i * 44), " ".join(ln), font=fz, fill=(66, 62, 62))

    # ══ серия и номер перфорацией по правому краю, дважды ══
    txt = "%s %s" % (p["passport_series"], p["passport_number"])
    for py in (250, MID + 210):
        perf = perforated(txt, font(F_BOLD, 54), PASSPORT_RED, dot=2, grid=4)
        perf = perf.rotate(90, expand=True)
        img.paste(perf, (W - perf.size[0] - 22, py), perf)

    return scanify(watermark(img, rnd), rnd)


# ───────────────────────── свидетельство ИНН ─────────────────────────

def ornament_border(d, w, h, pad, color):
    d.rectangle([pad, pad, w - pad, h - pad], outline=color, width=2)
    d.rectangle([pad + 14, pad + 14, w - pad - 14, h - pad - 14],
                outline=color, width=1)
    step = 18
    for x in range(pad + 14, w - pad - 14, step):
        d.arc([x, pad + 4, x + step, pad + 22], 180, 360, fill=color)
        d.arc([x, h - pad - 22, x + step, h - pad - 4], 0, 180, fill=color)
    for y in range(pad + 14, h - pad - 14, step):
        d.arc([pad + 4, y, pad + 22, y + step], 90, 270, fill=color)
        d.arc([w - pad - 22, y, w - pad - 4, y + step], 270, 90, fill=color)


def draw_inn(p, rnd):
    W, H = 1240, 1750
    img = paper(W, H, rnd, INN_PAPER)
    guilloche(img, INN_GUILLOCHE, amp=6, step=14, phase=0.4)
    rosette(img, W // 2, 1180, 300, (244, 230, 226))

    d = ImageDraw.Draw(img)
    ornament_border(d, W, H, 40, INN_ORNAMENT)

    f_small = font(F_SERIF, 22)
    f_txt = font(F_SERIF, 28)
    f_val = font(F_SERIF_BOLD, 32)

    # форма и код КНД
    d.text((W - 400, 84), "Форма № 2-1-Учет", font=font(F_SERIF, 24), fill=INK)
    d.text((W - 400, 116), "Код по КНД 1122022", font=font(F_SERIF, 24), fill=INK)

    rosette(img, W // 2, 128, 58, (176, 150, 148))
    d = ImageDraw.Draw(img)

    ctext(d, 218, "Федеральная налоговая служба", font(F_SERIF_BOLD, 34),
          (66, 60, 60), W)
    rule(d, 150, 272, W - 150, INN_ORNAMENT, 2)
    ctext(d, 292, "СВИДЕТЕЛЬСТВО", font(F_SERIF_BOLD, 62), INK, W)

    ctext(d, 402, "О ПОСТАНОВКЕ НА УЧЕТ ФИЗИЧЕСКОГО ЛИЦА",
          font(F_SERIF_BOLD, 27), INK, W)
    ctext(d, 440, "В НАЛОГОВОМ ОРГАНЕ", font(F_SERIF_BOLD, 27), INK, W)
    rule(d, 150, 486, W - 150, INN_ORNAMENT, 2)

    y = 556
    d.text((110, y + 6), "Настоящее свидетельство подтверждает, что",
           font=f_txt, fill=INK)
    d.text((660, y), p["fio"], font=f_val, fill=INK)
    rule(d, 650, y + 46, W - 110)

    y += 86
    d.text((110, y + 6), "пол", font=f_txt, fill=INK)
    d.text((176, y), p["sex"].strip(".").lower(), font=f_val, fill=INK)
    rule(d, 168, y + 46, 340)
    d.text((420, y + 6), "дата рождения", font=f_txt, fill=INK)
    d.text((660, y), p["birth"], font=f_val, fill=INK)
    rule(d, 650, y + 46, W - 110)

    y += 76
    d.text((110, y + 6), "место рождения", font=f_txt, fill=INK)
    d.text((370, y), p["birthplace"], font=f_val, fill=INK)
    rule(d, 360, y + 46, W - 110)

    y += 96
    for line in wrap(d, "поставлен(а) на учет в соответствии с Налоговым "
                        "кодексом Российской Федерации", f_txt, W - 220):
        d.text((110, y), line, font=f_txt, fill=INK)
        y += 42

    y += 40
    d.text((110, y + 6), "с присвоением", font=f_txt, fill=INK)
    d.text((350, y), p["tax_office"], font=font(F_SERIF_BOLD, 25), fill=INK)
    rule(d, 340, y + 46, W - 110)
    y += 76
    d.text((110, y + 8), "ИНН", font=font(F_SERIF_BOLD, 30), fill=INK)
    d.text((230, y), " ".join(p["inn"]), font=font(F_MONO_BOLD, 36), fill=INK)
    rule(d, 220, y + 50, W - 110)

    y += 130
    d.text((110, y + 30), "Заместитель начальника Инспекции",
           font=font(F_SERIF, 25), fill=INK)
    squiggle(d, 590, y + 44, 260, rnd, color=(58, 52, 96))
    rule(d, 580, y + 62, 880)
    d.text((900, y + 30), "М.П.", font=font(F_SERIF, 24), fill=INK)

    img = round_stamp(img, 745, y + 96, 132,
                      "ФНС РОССИИ ТЕСТОВАЯ", ["ОБРАЗЕЦ", "№ 9900"],
                      INN_STAMP, rnd, width=3)
    d = ImageDraw.Draw(img)

    # голограмма и серия бланка
    d.ellipse([150, H - 300, 300, H - 150], fill=(226, 212, 172),
              outline=HOLOGRAM, width=3)
    rosette(img, 225, H - 225, 62, (198, 178, 128))
    d = ImageDraw.Draw(img)
    d.text((820, H - 210), "серия", font=font(F_SERIF, 26), fill=INK)
    d.text((930, H - 216), p["inn_blank"], font=font(F_SERIF_BOLD, 30),
           fill=(150, 52, 52))
    rule(d, 920, H - 172, W - 110)

    return scanify(watermark(img, rnd), rnd)


# ───────────────────────── СНИЛС: зелёная карточка ─────────────────────────

def draw_snils(p, rnd):
    W, H = 1500, 1060
    img = paper(W, H, rnd, SNILS_PAPER)
    guilloche(img, SNILS_GUILLOCHE, amp=5, step=13, phase=1.1)

    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 46], fill=SNILS_BAND)
    d.rectangle([0, H - 46, W, H], fill=SNILS_BAND)
    d.rectangle([0, 250, W, 262], fill=(178, 200, 166))

    # орнаментальная колонна справа
    d.rectangle([W - 300, 46, W - 190, H - 46], fill=(208, 224, 198))
    for y in range(70, H - 60, 66):
        d.ellipse([W - 292, y, W - 198, y + 58], outline=(176, 198, 164))
    rosette(img, W - 245, H // 2 + 60, 130, (180, 202, 168))
    d = ImageDraw.Draw(img)

    f_lbl = font(F_SERIF_IT, 30)
    f_val = font(F_SERIF, 34)

    inner_w = W - 300
    ctext(d, 64, "Российская Федерация", font(F_SERIF, 32), SNILS_INK, inner_w)
    ctext(d, 108, "СТРАХОВОЕ СВИДЕТЕЛЬСТВО", font(F_SERIF_BOLD, 46),
          SNILS_INK, inner_w)
    ctext(d, 176, "ОБЯЗАТЕЛЬНОГО ПЕНСИОННОГО СТРАХОВАНИЯ",
          font(F_SERIF, 30), SNILS_INK, inner_w)

    ctext(d, 292, p["snils"], font(F_SERIF_BOLD, 52), SNILS_INK, inner_w)

    y = 396
    d.text((90, y + 6), "Ф.И.О.", font=f_lbl, fill=SNILS_INK)
    for part in (p["surname"].upper(), p["name"].upper(), p["patronymic"].upper()):
        d.text((300, y), part, font=f_val, fill=SNILS_INK)
        y += 52

    y += 24
    d.text((90, y + 4), "Дата и место рождения", font=f_lbl, fill=SNILS_INK)
    d.text((560, y), words_date(p["birth"], upper=True), font=f_val, fill=SNILS_INK)
    y += 52
    d.text((560, y), p["birthplace"], font=font(F_SERIF, 30), fill=SNILS_INK)

    y += 96
    d.text((90, y + 4), "Пол", font=f_lbl, fill=SNILS_INK)
    d.text((300, y), "мужской" if p["sex"].startswith("М") else "женский",
           font=f_val, fill=SNILS_INK)
    y += 56
    d.text((90, y + 4), "Дата регистрации", font=f_lbl, fill=SNILS_INK)
    d.text((470, y), words_date(p["snils_registered_at"], with_goda=True),
           font=f_val, fill=SNILS_INK)

    return scanify(watermark(img, rnd, size_div=11), rnd, fill=(248, 250, 244))


# ───────────────────────── сборка ─────────────────────────

def slug(p):
    return "%s_%s_%s" % (p["surname"], p["name"], p["patronymic"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=4, help="сколько комплектов")
    ap.add_argument("--seed", type=int, default=20261008, help="зерно генератора")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()

    d_sets = os.path.join(a.out, "комплекты")
    d_truth = os.path.join(a.out, "эталон")
    os.makedirs(d_sets, exist_ok=True)
    os.makedirs(d_truth, exist_ok=True)

    # Два независимых потока случайных чисел. Данные не должны съезжать
    # от правок в отрисовке — иначе эталон меняется при каждой косметике.
    data_rnd = random.Random(a.seed)
    for i in range(a.count):
        p = make_person(i, data_rnd)
        name = "%02d_%s" % (i + 1, slug(p))
        folder = os.path.join(d_sets, name)
        os.makedirs(folder, exist_ok=True)

        rnd = random.Random(a.seed * 7919 + i)
        draw_passport(p, rnd).save(os.path.join(folder, "паспорт.png"))
        draw_inn(p, rnd).save(os.path.join(folder, "инн.png"))
        draw_snils(p, rnd).save(os.path.join(folder, "снилс.png"))

        with open(os.path.join(d_truth, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(p, f, ensure_ascii=False, indent=2)

        print("готово:", name)

    print("\nкомплекты: %s\nэталон:    %s" % (d_sets, d_truth))


if __name__ == "__main__":
    main()

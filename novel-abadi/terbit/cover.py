#!/usr/bin/env python3
"""Sampul novel: plat ilmiah berlatar terang. Enam tahap siklus sel
(interfase, profase, metafase, anafase, telofase, sitokinesis) mengelilingi
heliks DNA, digambar bergaya diagram buku biologi dengan warna cerah.

Hanya memakai Pillow; hasil deterministik.
    python3 cover.py "Baris1|Baris2" "Nama Penulis" keluaran.jpg
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1600, 2400
S = 2                                        # supersampling
FD = "/usr/share/fonts/opentype/linux-libertine/"
RC, RR, CR = (800, 1520), 455, 128           # pusat cincin, jari-jari cincin, jari-jari sel

NAVY = (27, 38, 74)
MAGENTA = (226, 48, 134)
CYAN = (22, 160, 216)
ORANGE = (245, 150, 24)
GREEN = (66, 182, 104)
VIOLET = (112, 80, 196)
YELLOW = (250, 200, 40)
CHROMS = [MAGENTA, CYAN, ORANGE, GREEN, VIOLET]


def font(name, size):
    return ImageFont.truetype(FD + name, size)


def mix(c, t, base=(255, 255, 255)):
    """Campur warna c dengan putih: t=0 -> c, t=1 -> putih."""
    return tuple(int(c[i] * (1 - t) + base[i] * t) for i in range(3))


class Pen:
    """Penggambar dengan koordinat logis (W x H) pada kanvas S kali lebih besar."""

    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    def circle(self, x, y, r, fill=None, outline=None, width=0):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
                       fill=fill, outline=outline, width=int(width * S))

    def ellipse(self, x, y, rx, ry, fill=None, outline=None, width=0):
        self.d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S],
                       fill=fill, outline=outline, width=int(width * S))

    def line(self, pts, fill, width, round_caps=True):
        sp = [(x * S, y * S) for x, y in pts]
        self.d.line(sp, fill=fill, width=int(width * S), joint="curve")
        if round_caps:
            for (x, y) in (pts[0], pts[-1]):
                self.circle(x, y, width / 2, fill=fill)

    def poly(self, pts, fill=None, outline=None, width=0):
        sp = [(x * S, y * S) for x, y in pts]
        if fill:
            self.d.polygon(sp, fill=fill)
        if outline:
            self.line(pts + [pts[0]], outline, width)


def chromosome(p, x, y, size, ang, col):
    """Kromosom berbentuk X (dua kromatid dengan sentromer)."""
    a = math.radians(ang)
    for s in (+1, -1):
        b = a + s * math.radians(24)
        dx, dy = math.cos(b) * size, math.sin(b) * size
        p.line([(x - dx, y - dy), (x + dx, y + dy)], col, size * 0.34)
    p.circle(x, y, size * 0.2, fill=mix(col, 0.35))


def chromatid_v(p, x, y, size, toward, col):
    """Kromatid anafase: V dengan ujung menuju kutub (toward = +1 kanan / -1 kiri)."""
    for s in (+1, -1):
        p.line([(x, y), (x - toward * size * 0.75, y + s * size * 0.8)], col, size * 0.3)
    p.circle(x, y, size * 0.2, fill=mix(col, 0.35))


def nucleus(p, x, y, r, col=VIOLET, squiggles=True):
    p.circle(x, y, r, fill=mix(col, 0.72), outline=col, width=r * 0.09)
    p.circle(x - r * 0.18, y - r * 0.12, r * 0.24, fill=mix(col, 0.15))      # anak inti
    if squiggles:
        rng = random.Random(int(x * 7 + y))
        for _ in range(5):
            a = rng.uniform(0, 2 * math.pi)
            sx, sy = x + r * 0.45 * math.cos(a), y + r * 0.45 * math.sin(a)
            pts = [(sx + k * r * 0.08 * (1 if rng.random() < 0.5 else -1) + r * 0.06 * math.sin(k),
                    sy + k * r * 0.07 + r * 0.05 * math.cos(k * 1.7)) for k in range(5)]
            p.line(pts, mix(col, 0.15), r * 0.045)


def mitochondrion(p, x, y, size, ang):
    a = math.radians(ang)
    cs, sn = math.cos(a), math.sin(a)
    pts = []
    for k in range(24):
        t = 2 * math.pi * k / 24
        ex, ey = size * math.cos(t), size * 0.5 * math.sin(t)
        pts.append((x + ex * cs - ey * sn, y + ex * sn + ey * cs))
    p.poly(pts, fill=mix(ORANGE, 0.45), outline=ORANGE, width=size * 0.14)
    p.line([(x - cs * size * 0.5, y - sn * size * 0.5), (x + cs * size * 0.5, y + sn * size * 0.5)],
           mix(ORANGE, 0.1), size * 0.1, round_caps=False)


def membrane_cell(p, x, y, rx, ry, col):
    p.ellipse(x, y, rx, ry, fill=mix(col, 0.82), outline=col, width=6)
    p.ellipse(x, y, rx - 12, ry - 12, outline=mix(col, 0.55), width=2)


def dumbbell(x, y, rx, ry, pinch):
    pts = []
    n = 60
    for k in range(n + 1):
        px = -rx + 2 * rx * k / n
        h = ry * math.sqrt(max(0.0, 1 - (px / rx) ** 2)) * (1 - pinch * math.exp(-(px / (0.28 * rx)) ** 2))
        pts.append((x + px, y - h))
    for k in range(n, -1, -1):
        px = -rx + 2 * rx * k / n
        h = ry * math.sqrt(max(0.0, 1 - (px / rx) ** 2)) * (1 - pinch * math.exp(-(px / (0.28 * rx)) ** 2))
        pts.append((x + px, y + h))
    return pts


def stage(p, kind, x, y, r, col):
    if kind == "interfase":
        membrane_cell(p, x, y, r, r, col)
        for (a, d, s, an) in ((200, 0.78, 20, 20), (320, 0.74, 18, -40), (95, 0.78, 19, 70), (20, 0.8, 16, 10)):
            mitochondrion(p, x + r * d * math.cos(math.radians(a)), y + r * d * math.sin(math.radians(a)), s, an)
        nucleus(p, x, y, r * 0.5)
    elif kind == "profase":
        membrane_cell(p, x, y, r, r, col)
        for k in range(36):                                  # selaput inti putus-putus
            if k % 2 == 0:
                a0, a1 = 2 * math.pi * k / 36, 2 * math.pi * (k + 1) / 36
                p.line([(x + r * 0.55 * math.cos(a0 + t * (a1 - a0)), y + r * 0.55 * math.sin(a0 + t * (a1 - a0)))
                        for t in (0, .5, 1)], VIOLET, 3.5, round_caps=False)
        for i, (dx, dy, an) in enumerate(((-0.22, -0.18, 20), (0.2, -0.22, 80), (-0.12, 0.2, 140), (0.24, 0.16, 55))):
            chromosome(p, x + r * dx, y + r * dy, r * 0.22, an, CHROMS[i])
        for sx in (-1, 1):
            p.circle(x + sx * r * 0.76, y - r * 0.05, 6.5, fill=NAVY)
    elif kind == "metafase":
        membrane_cell(p, x, y, r, r, col)
        poles = [(x - r * 0.82, y), (x + r * 0.82, y)]
        ys = [-0.56, -0.28, 0, 0.28, 0.56]
        for i, dy in enumerate(ys):
            for (px, py) in poles:
                p.line([(px, py), (x, y + r * dy)], mix(NAVY, 0.55), 2.2, round_caps=False)
        for px, py in poles:
            p.circle(px, py, 7, fill=NAVY)
        for i, dy in enumerate(ys):
            chromosome(p, x, y + r * dy, r * 0.17, 90 + (i - 2) * 6, CHROMS[i % 5])
    elif kind == "anafase":
        rx, ry = r * 1.22, r * 0.92
        membrane_cell(p, x, y, rx, ry, col)
        poles = [(x - rx * 0.86, y), (x + rx * 0.86, y)]
        ys = [-0.5, -0.25, 0, 0.25, 0.5]
        for i, dy in enumerate(ys):
            for side, (px, py) in zip((-1, 1), poles):
                p.line([(px, py), (x + side * rx * 0.38, y + ry * dy)], mix(NAVY, 0.55), 2.2, round_caps=False)
        for px, py in poles:
            p.circle(px, py, 7, fill=NAVY)
        for i, dy in enumerate(ys):
            for side in (-1, 1):
                chromatid_v(p, x + side * rx * 0.38, y + ry * dy, r * 0.17, side, CHROMS[i % 5])
    elif kind == "telofase":
        rx, ry = r * 1.28, r * 0.86
        pts = dumbbell(x, y, rx, ry, 0.42)
        p.poly(pts, fill=mix(col, 0.82), outline=col, width=6)
        for sx in (-1, 1):
            nucleus(p, x + sx * rx * 0.52, y, r * 0.36, squiggles=False)
            mitochondrion(p, x + sx * rx * 0.5, y + r * 0.6 * (1 if sx < 0 else -1), 13, 25 * sx)
    elif kind == "sitokinesis":
        for sx in (-1, 1):
            cx = x + sx * r * 0.66
            membrane_cell(p, cx, y, r * 0.66, r * 0.66, col)
            nucleus(p, cx, y, r * 0.32, squiggles=False)
            mitochondrion(p, cx + sx * r * 0.28, y + r * 0.38, 12, -20 * sx)


def arrow_arc(p, a0, a1, col):
    pts = []
    n = 14
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((RC[0] + RR * math.cos(a), RC[1] + RR * math.sin(a)))
    p.line(pts, col, 5)
    (x1, y1), (x0, y0) = pts[-1], pts[-3]
    ang = math.atan2(y1 - y0, x1 - x0)
    tip = (x1 + math.cos(ang) * 14, y1 + math.sin(ang) * 14)
    wing = [(x1 + math.cos(ang + s * 2.5) * 22, y1 + math.sin(ang + s * 2.5) * 22) for s in (-1, 1)]
    p.poly([tip, wing[0], wing[1]], fill=col)


def helix(p, cx, cy, half_h, amp, turns):
    items = []
    n = 220
    for k in range(n + 1):
        t = k / n
        y = cy - half_h + 2 * half_h * t
        ph = 2 * math.pi * turns * t
        xa, za = cx + amp * math.sin(ph), math.cos(ph)
        xb, zb = cx - amp * math.sin(ph), -math.cos(ph)
        items.append((za, "s", xa, y, MAGENTA, za))
        items.append((zb, "s", xb, y, CYAN, zb))
        if k % 7 == 3:
            c1, c2 = ((ORANGE, GREEN), (YELLOW, VIOLET))[(k // 7) % 2]
            items.append((0, "r", xa, y, (xb, c1, c2), 0))
    items.sort(key=lambda it: it[0])
    for z, kind, x, y, col, depth in items:
        if kind == "s":
            p.circle(x, y, 10 + 3.5 * depth, fill=mix(col, 0.0 if depth > 0 else 0.28))
        else:
            xb, c1, c2 = col
            xm = (x + xb) / 2
            p.line([(x, y), (xm, y)], c1, 7)
            p.line([(xm, y), (xb, y)], c2, 7)


def background(rng):
    img = Image.new("RGB", (W * S, H * S))
    d = ImageDraw.Draw(img)
    top, bot = (252, 248, 239), (243, 235, 221)
    for y in range(0, H * S, 4):
        t = y / (H * S - 1)
        d.rectangle([0, y, W * S, y + 4], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    p = Pen(img)
    # halo di balik cincin, bergaya lensa mikroskop
    p.circle(RC[0], RC[1], 640, fill=(255, 253, 249))
    p.circle(RC[0], RC[1], 640, outline=mix(CYAN, 0.7), width=3)
    p.circle(RC[0], RC[1], 622, outline=mix(MAGENTA, 0.8), width=2)
    for k in range(120):
        a = 2 * math.pi * k / 120
        l = 18 if k % 5 == 0 else 9
        p.line([(RC[0] + 640 * math.cos(a), RC[1] + 640 * math.sin(a)),
                (RC[0] + (640 + l) * math.cos(a), RC[1] + (640 + l) * math.sin(a))], mix(NAVY, 0.55), 2.5, round_caps=False)
    # konfeti: sel dan molekul kecil pucat
    cols = [MAGENTA, CYAN, ORANGE, GREEN, VIOLET, YELLOW]
    placed = 0
    while placed < 70:
        x, y = rng.randrange(90, W - 90), rng.randrange(90, H - 90)
        if math.hypot(x - RC[0], y - RC[1]) < 700 or (y < 880 and 120 < x < W - 120) or y > 2240:
            continue
        c = rng.choice(cols)
        r = rng.choice((10, 14, 20, 28, 40))
        if rng.random() < 0.55:
            p.circle(x, y, r, fill=mix(c, 0.78), outline=mix(c, 0.35), width=3)
            p.circle(x + r * 0.15, y - r * 0.1, r * 0.38, fill=mix(c, 0.35))
        else:
            p.line([(x - r, y), (x + r, y)], mix(c, 0.35), 4)
            p.line([(x, y - r), (x, y + r)], mix(c, 0.35), 4)
        placed += 1
    return img, p


def draw_plate(p):
    kinds = ["interfase", "profase", "metafase", "anafase", "telofase", "sitokinesis"]
    names = ["Interfase", "Profase", "Metafase", "Anafase", "Telofase", "Sitokinesis"]
    accents = [CYAN, VIOLET, MAGENTA, ORANGE, GREEN, CYAN]
    angs = [-90, -30, 30, 90, 150, 210]
    for a in angs:                                    # panah antar tahap
        arrow_arc(p, a + 25, a + 35, mix(NAVY, 0.25))
    # heliks DNA di tengah, dalam lingkaran perbesaran
    p.circle(RC[0], RC[1], 262, fill=(255, 255, 255), outline=mix(NAVY, 0.4), width=3)
    p.circle(RC[0], RC[1], 248, outline=mix(YELLOW, 0.3), width=2)
    helix(p, RC[0], RC[1], 205, 66, 2.6)
    lab = ImageFont.truetype(FD + "LinLibertine_RI.otf", 40 * S)
    for i, a in enumerate(angs):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        stage(p, kinds[i], RC[0] + RR * ca, RC[1] + RR * sa, CR, accents[i])
        txt = f"{i + 1}  {names[i]}"
        w = p.d.textlength(txt, font=lab) / S
        cx, cy = RC[0] + RR * ca, RC[1] + RR * sa
        above = sa < 0.2 and not (a == 90)          # sel di bagian atas: label di atasnya
        reach = CR + 34
        ty = cy - reach - 24 if above else cy + reach - 20
        p.d.text(((cx - w / 2) * S, ty * S), txt, font=lab, fill=NAVY)


def draw_text(p, title_lines, author, subtitle="SEBUAH NOVEL"):
    def centered(txt, y, f, fill, track=0):
        if track:
            widths = [p.d.textlength(ch, font=f) / S for ch in txt]
            total = sum(widths) + track * (len(txt) - 1)
            x = (W - total) / 2
            for ch, w in zip(txt, widths):
                p.d.text((x * S, y * S), ch, font=f, fill=fill)
                x += w + track
        else:
            p.d.text(((W - p.d.textlength(txt, font=f) / S) / 2 * S, y * S), txt, font=f, fill=fill)

    centered(subtitle, 118, font("LinLibertine_R.otf", 44 * S), mix(NAVY, 0.25), track=16)
    y = 175
    cols = [NAVY, MAGENTA]
    for i, (txt, size) in enumerate(title_lines):
        centered(txt, y, font("LinLibertine_RBI.otf", size * S), cols[i % 2])
        y += int(size * 1.0)
    centered(author.upper(), H - 150, font("LinLibertine_R.otf", 66 * S), NAVY, track=20)


def frame(p):
    p.d.rectangle([48 * S, 48 * S, (W - 48) * S, (H - 48) * S], outline=mix(NAVY, 0.3), width=3 * S)
    p.d.rectangle([62 * S, 62 * S, (W - 62) * S, (H - 62) * S], outline=mix(MAGENTA, 0.5), width=2 * S)


def make_cover(title_lines, author, path):
    rng = random.Random(2002)
    img, p = background(rng)
    draw_plate(p)
    draw_text(p, title_lines, author)
    frame(p)
    img = img.resize((W, H), Image.LANCZOS)
    noise = Image.effect_noise((W, H), 12).convert("RGB")
    noise = ImageEnhance.Contrast(noise).enhance(0.25)
    img = ImageChops.add(img, noise, scale=1.0, offset=-128 + 2)
    path = Path(path)
    if path.suffix.lower() in (".jpg", ".jpeg"):
        img.save(path, quality=93, optimize=True, subsampling=0)
    else:
        img.save(path)
    return path


if __name__ == "__main__":
    spec = sys.argv[1].split("|")
    sizes = [260, 340, 260]
    make_cover(list(zip(spec, sizes)), sys.argv[2], sys.argv[3])

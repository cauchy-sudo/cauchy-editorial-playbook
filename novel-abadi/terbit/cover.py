#!/usr/bin/env python3
"""Sampul novel: plat ilmiah bergaya tenang. Satu heliks DNA membelah menjadi dua
(replikasi): untai induk berwarna biru tinta, untai baru berwarna merah tua,
di atas kertas krem, dengan keterangan bergaya buku biologi lama.

Hanya memakai Pillow; hasil deterministik.
    python3 cover.py "Judul" "Nama Penulis" keluaran.jpg
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1600, 2400
S = 2                                        # supersampling
FD = "/usr/share/fonts/opentype/linux-libertine/"

PAPER_TOP, PAPER_BOT = (247, 242, 230), (238, 230, 214)
INK = (22, 34, 62)                           # biru tinta: untai induk, teks
RED = (150, 38, 46)                          # merah tua: untai baru
RUNG = (150, 128, 92)                        # pasangan basa: cokelat keemasan, redup
Y0, Y1 = 640, 2020                            # rentang vertikal heliks
FORK_Y = 1270                                # tempat heliks mulai membelah
FORK_LEN = 720                               # panjang transisi garpu
TURNS, AMP, DAUGHTER = 3.7, 150, 270
AXIS_X = W // 2


def mix(c, t, base=(255, 255, 255)):
    return tuple(int(c[i] * (1 - t) + base[i] * t) for i in range(3))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Pen:
    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    def circle(self, x, y, r, fill=None, outline=None, width=0):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
                       fill=fill, outline=outline, width=int(width * S))

    def line(self, pts, fill, width, round_caps=True):
        sp = [(x * S, y * S) for x, y in pts]
        self.d.line(sp, fill=fill, width=max(1, int(width * S)), joint="curve")
        if round_caps:
            for (x, y) in (pts[0], pts[-1]):
                self.circle(x, y, width / 2, fill=fill)

    def text(self, xy, txt, f, fill):
        self.d.text((xy[0] * S, xy[1] * S), txt, font=f, fill=fill)

    def width(self, txt, f):
        return self.d.textlength(txt, font=f) / S


def font(name, size):
    return ImageFont.truetype(FD + name, int(size * S))


# --------------------------------------------------------------- latar
def background():
    img = Image.new("RGB", (W * S, H * S))
    d = ImageDraw.Draw(img)
    for y in range(0, H * S, 4):
        t = y / (H * S - 1)
        d.rectangle([0, y, W * S, y + 4],
                    fill=tuple(int(PAPER_TOP[i] + (PAPER_BOT[i] - PAPER_TOP[i]) * t) for i in range(3)))
    p = Pen(img)
    # lingkaran bidang pandang yang sangat samar, dengan skala tipis
    cx, cy, R = AXIS_X, 1420, 650
    p.circle(cx, cy, R, outline=mix(INK, 0.82), width=2.5)
    p.circle(cx, cy, R - 16, outline=mix(INK, 0.9), width=1.5)
    for k in range(180):
        a = 2 * math.pi * k / 180
        l = 16 if k % 5 == 0 else 8
        p.line([(cx + R * math.cos(a), cy + R * math.sin(a)),
                (cx + (R + l) * math.cos(a), cy + (R + l) * math.sin(a))], mix(INK, 0.7), 2, round_caps=False)
    return img, p


# --------------------------------------------------------------- heliks
def strand_pos(y, which):
    """Posisi x untai pada tinggi y. which: 'a','b' (induk) atau 'a2','b2' (baru)."""
    t = (y - Y0) / (Y1 - Y0)
    ph = 2 * math.pi * TURNS * t
    sp = smooth((y - FORK_Y) / FORK_LEN)
    amp = AMP * (1 - 0.15 * sp)
    sa = math.sin(ph)
    return {"a": AXIS_X - sp * DAUGHTER + amp * sa,
            "b": AXIS_X + sp * DAUGHTER - amp * sa,
            "a2": AXIS_X - sp * DAUGHTER - amp * sa,
            "b2": AXIS_X + sp * DAUGHTER + amp * sa}[which], math.cos(ph), sp


def helix_items():
    items = []
    n = 1100
    for k in range(n + 1):
        y = Y0 + (Y1 - Y0) * k / n
        xa, ca, sp = strand_pos(y, "a")
        xb, _, _ = strand_pos(y, "b")
        items.append((ca, "s", xa, y, INK, ca, 1.0))
        items.append((-ca, "s", xb, y, INK, -ca, 1.0))
        if y > FORK_Y + 40:                                # untai baru tumbuh sesudah garpu
            grow = smooth((y - FORK_Y - 40) / 220)
            xa2, _, _ = strand_pos(y, "a2")
            xb2, _, _ = strand_pos(y, "b2")
            items.append((-ca, "s", xa2, y, RED, -ca, grow))
            items.append((ca, "s", xb2, y, RED, ca, grow))
        if k % 14 == 5:                                    # pasangan basa
            if y < FORK_Y:
                items.append((0, "r", xa, y, xb, 1.0, 1.0))
            elif y > FORK_Y + 40:
                g = smooth((y - FORK_Y - 40) / 260)
                xa2, _, _ = strand_pos(y, "a2")
                xb2, _, _ = strand_pos(y, "b2")
                items.append((0, "r", xa, y, xa2, 1.0, g))
                items.append((0, "r", xb, y, xb2, 1.0, g))
    items.sort(key=lambda it: it[0])
    return items


def draw_helix(p):
    for depth, kind, x, y, c, z, grow in helix_items():
        if kind == "s":
            col = c if z > 0 else mix(c, 0.35)
            r = (10 + 3.6 * z) * (0.35 + 0.65 * grow)
            p.circle(x, y, r, fill=col)
            if z > 0.55:                                  # kilap tipis pada sisi depan
                p.circle(x - r * 0.28, y - r * 0.3, r * 0.28, fill=mix(col, 0.55))
        else:
            xa, xb = x, c
            p.line([(xa, y), (xb, y)], mix(RUNG, 0.1 if grow > 0.5 else 0.35), 5 * (0.4 + 0.6 * grow))


def paper_fade(img, y_from, y_to, top_to_bottom):
    """Timpa pita [y_from, y_to] dengan warna kertas, makin pekat ke arah ujung."""
    h = (y_to - y_from) * S
    grad = Image.new("L", (W * S, h))
    gd = ImageDraw.Draw(grad)
    for i in range(h):
        t = i / max(1, h - 1)
        a = int(255 * (1 - t if top_to_bottom else t))
        gd.line([(0, i), (W * S, i)], fill=a)
    # warna kertas pada tinggi tersebut
    paper = Image.new("RGB", (W * S, h))
    pd = ImageDraw.Draw(paper)
    for i in range(h):
        y = y_from + i / S
        t = y / (H - 1)
        pd.line([(0, i), (W * S, i)], fill=tuple(int(PAPER_TOP[j] + (PAPER_BOT[j] - PAPER_TOP[j]) * t) for j in range(3)))
    region = img.crop((0, y_from * S, W * S, y_to * S))
    img.paste(Image.composite(paper, region, grad), (0, y_from * S))


# --------------------------------------------------------------- keterangan ilmiah
def annotations(p):
    f = font("LinLibertine_RI.otf", 38)
    ink = mix(INK, 0.15)
    thin = mix(INK, 0.3)

    def label(txt, anchor, text_xy, align):
        w = p.width(txt, f)
        tx = text_xy[0] if align == "left" else text_xy[0] - w
        p.text((tx, text_xy[1] - 24), txt, f, ink)
        ex = tx + w + 14 if align == "left" else tx - 14
        p.line([(ex, text_xy[1]), anchor], thin, 2, round_caps=False)
        p.circle(anchor[0], anchor[1], 6, fill=ink)

    y_a = 900
    xa, _, _ = strand_pos(y_a, "a")
    label("untai induk", (xa, y_a), (150, 760), "left")
    y_r = Y0 + (Y1 - Y0) * (14 * 20 + 5) / 1100            # sebuah pasangan basa di bagian induk
    label("pasangan basa", (AXIS_X, y_r), (W - 150, 880), "right")
    label("garpu replikasi", (AXIS_X, FORK_Y + 40), (W - 150, 1260), "right")
    y_n = max(range(1640, 1900, 2), key=lambda y: abs(strand_pos(y, "a2")[0] - AXIS_X) - 0.0)   # untai merah terluar
    xn, _, _ = strand_pos(y_n, "a2")
    label("untai baru", (xn, y_n), (150, 1640), "left")


# --------------------------------------------------------------- teks
def tracked(p, txt, y, f, fill, track):
    widths = [p.width(ch, f) for ch in txt]
    total = sum(widths) + track * (len(txt) - 1)
    x = (W - total) / 2
    for ch, w in zip(txt, widths):
        p.text((x, y), ch, f, fill)
        x += w + track


def draw_text(p, title, author):
    tracked(p, title.upper(), 190, font("LinLibertine_R.otf", 300), INK, 46)
    p.line([(W / 2 - 90, 565), (W / 2 + 90, 565)], RED, 4, round_caps=False)
    tracked(p, author.upper(), H - 215, font("LinLibertine_R.otf", 62), INK, 22)


def frame(p):
    p.d.rectangle([54 * S, 54 * S, (W - 54) * S, (H - 54) * S], outline=mix(INK, 0.35), width=3 * S)
    p.d.rectangle([68 * S, 68 * S, (W - 68) * S, (H - 68) * S], outline=mix(RED, 0.55), width=2 * S)


def make_cover(title, author, path):
    img, p = background()
    draw_helix(p)
    paper_fade(img, Y0 - 30, Y0 + 130, True)       # ujung atas memudar
    paper_fade(img, Y1 - 150, Y1 + 20, False)      # ujung bawah memudar
    p = Pen(img)
    annotations(p)
    draw_text(p, title, author)
    frame(p)
    img = img.resize((W, H), Image.LANCZOS)
    noise = Image.effect_noise((W, H), 14).convert("RGB")
    noise = ImageEnhance.Contrast(noise).enhance(0.25)
    img = ImageChops.add(img, noise, scale=1.0, offset=-128 + 2)
    path = Path(path)
    if path.suffix.lower() in (".jpg", ".jpeg"):
        img.save(path, quality=93, optimize=True, subsampling=0)
    else:
        img.save(path)
    return path


if __name__ == "__main__":
    make_cover(sys.argv[1], sys.argv[2], sys.argv[3])

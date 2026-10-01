#!/usr/bin/env python3
"""Sampul novel: seekor kupu-kupu yang tersusun dari sel-sel berpendar,
seperti foto mikroskop imunofluoresensi (inti sel, membran, mitokondria).

Hanya memakai Pillow. Hasil deterministik (seed tetap).
    python3 cover.py "Judul|baris|baris" "Nama Penulis" keluaran.jpg
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1600, 2400
SS = 2                                   # supersampling lapisan sel
FD = "/usr/share/fonts/opentype/linux-libertine/"
CX, CY = W // 2, 1440                    # pusat kupu-kupu


def font(name, size):
    return ImageFont.truetype(FD + name, size)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def teardrop(cx, cy, a, b, angle, skew=0.28, n=240):
    """Poligon sayap: elips yang meruncing ke satu ujung, diputar `angle`."""
    pts = []
    ca, sa = math.cos(angle), math.sin(angle)
    for k in range(n):
        t = 2 * math.pi * k / n
        x = a * math.cos(t)
        y = b * math.sin(t) * (1 - skew * math.cos(t))
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def wing_polys():
    """(sayap atas, sayap bawah) untuk sisi kanan; sisi kiri dicerminkan."""
    up = teardrop(CX + 318, CY - 195, 430, 245, math.radians(-34), skew=-0.42)
    lo = teardrop(CX + 235, CY + 265, 300, 175, math.radians(38), skew=-0.30)
    return up, lo


def mirror(poly):
    return [(2 * CX - x, y) for x, y in poly]


def make_masks():
    up, lo = wing_polys()
    m_up = Image.new("L", (W, H), 0)
    m_lo = Image.new("L", (W, H), 0)
    m_bd = Image.new("L", (W, H), 0)
    for poly in (up, mirror(up)):
        ImageDraw.Draw(m_up).polygon(poly, fill=255)
    for poly in (lo, mirror(lo)):
        ImageDraw.Draw(m_lo).polygon(poly, fill=255)
    d = ImageDraw.Draw(m_bd)
    d.ellipse([CX - 36, CY - 330, CX + 36, CY - 200], fill=255)          # kepala + dada
    d.ellipse([CX - 44, CY - 230, CX + 44, CY + 180], fill=255)          # toraks
    d.ellipse([CX - 34, CY + 120, CX + 34, CY + 470], fill=255)          # perut
    return m_up, m_lo, m_bd


def place_cells(masks, rng):
    m_up, m_lo, m_bd = masks
    cells, grid, g = [], {}, 40
    px = {k: m.load() for k, m in zip("ulb", masks)}

    def region(x, y):
        if not (0 <= x < W and 0 <= y < H):
            return None
        if px["b"][x, y]:
            return "b"
        if px["u"][x, y]:
            return "u"
        if px["l"][x, y]:
            return "l"
        return None

    def free(x, y, r):
        gx, gy = int(x // g), int(y // g)
        for i in range(gx - 2, gx + 3):
            for j in range(gy - 2, gy + 3):
                for (ox, oy, orr) in grid.get((i, j), ()):
                    if (ox - x) ** 2 + (oy - y) ** 2 < (orr + r - 3) ** 2:
                        return False
        return True

    for rad_hi, rad_lo, tries in ((46, 30, 9000), (30, 18, 22000), (18, 11, 40000)):
        for _ in range(tries):
            x, y = rng.randrange(CX - 760, CX + 760), rng.randrange(CY - 520, CY + 560)
            r = rng.uniform(rad_lo, rad_hi)
            reg = region(x, y)
            if reg is None:
                continue
            # tepi sel harus berada di dalam bentuk (uji 8 titik)
            ok = True
            for a in range(0, 360, 45):
                if region(int(x + r * 0.9 * math.cos(math.radians(a))),
                          int(y + r * 0.9 * math.sin(math.radians(a)))) is None:
                    ok = False
                    break
            if not ok or not free(x, y, r):
                continue
            cells.append((x, y, r, reg))
            grid.setdefault((int(x // g), int(y // g)), []).append((x, y, r))
    return cells


PAL = {
    "u_in": (255, 70, 175), "u_out": (255, 165, 40),     # sayap atas: magenta -> jingga
    "l_in": (40, 190, 255), "l_out": (110, 245, 120),    # sayap bawah: sian -> hijau
    "b": (255, 214, 90),                                  # tubuh: kuning emas
}


def cell_color(x, y, reg, rng):
    dist = abs(x - CX)
    if reg == "u":
        t = min(1.0, max(0.0, (dist - 60) / 640))
        c = lerp(PAL["u_in"], PAL["u_out"], t)
    elif reg == "l":
        t = min(1.0, max(0.0, (dist - 40) / 420))
        c = lerp(PAL["l_in"], PAL["l_out"], t)
    else:
        c = PAL["b"]
    j = rng.uniform(-18, 18)
    return tuple(max(0, min(255, int(v + j))) for v in c)


def draw_cell(d, x, y, r, col, rng):
    s = SS
    X, Y, R = x * s, y * s, r * s
    dark = tuple(int(v * 0.12) for v in col)
    mid = tuple(int(v * 0.30) for v in col)
    d.ellipse([X - R, Y - R, X + R, Y + R], fill=dark)
    d.ellipse([X - R * 0.86, Y - R * 0.86, X + R * 0.86, Y + R * 0.86], fill=mid)
    d.ellipse([X - R, Y - R, X + R, Y + R], outline=col, width=max(2, int(R * 0.09)))
    # mitokondria: lonjong kecil di cincin luar
    if r > 17:
        for _ in range(rng.randint(3, 6)):
            a = rng.uniform(0, 2 * math.pi)
            dd = R * rng.uniform(0.58, 0.78)
            mx, my = X + dd * math.cos(a), Y + dd * math.sin(a)
            mr = R * 0.09
            mit = (255, 235, 150) if rng.random() < 0.5 else (255, 140, 60)
            d.ellipse([mx - mr * 1.8, my - mr, mx + mr * 1.8, my + mr], fill=mit)
    # inti sel (biru-ungu seperti pewarna DAPI), sedikit bergeser
    nr = R * rng.uniform(0.34, 0.44)
    nx, ny = X + R * rng.uniform(-0.1, 0.1), Y + R * rng.uniform(-0.1, 0.1)
    nuc = (rng.randint(70, 110), rng.randint(110, 150), 255)
    d.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=nuc)
    if r > 15:
        k = nr * 0.32
        d.ellipse([nx - k * 0.6, ny - k * 0.4, nx + k * 0.6, ny + k * 0.8], fill=(20, 28, 90))


def background(rng):
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    top, mid, bot = (10, 14, 38), (24, 20, 58), (8, 26, 44)
    for y in range(H):
        t = y / (H - 1)
        c = lerp(top, mid, t * 2) if t < 0.5 else lerp(mid, bot, (t - 0.5) * 2)
        d.line([(0, y), (W, y)], fill=tuple(int(v) for v in c))
    # sel di luar fokus, besar dan samar
    far = Image.new("RGB", (W, H), (0, 0, 0))
    fd = ImageDraw.Draw(far)
    cols = [(120, 40, 140), (30, 90, 150), (150, 70, 40), (30, 120, 100), (90, 50, 160)]
    for _ in range(46):
        x, y = rng.randrange(-100, W + 100), rng.randrange(-100, H + 100)
        r = rng.randint(50, 190)
        c = rng.choice(cols)
        fd.ellipse([x - r, y - r, x + r, y + r], outline=c, width=rng.randint(6, 16))
        if rng.random() < 0.7:
            q = int(r * 0.35)
            fd.ellipse([x - q, y - q, x + q, y + q], fill=tuple(int(v * 0.8) for v in c))
    far = far.filter(ImageFilter.GaussianBlur(26))
    far = ImageEnhance.Brightness(far).enhance(0.75)
    return ImageChops.screen(bg, far)


def vignette(img):
    mask = Image.radial_gradient("L").resize((W, H))           # 0 di pusat, 255 di tepi
    mask = mask.point(lambda v: int(max(0, v - 90) * 0.9))
    black = Image.new("RGB", (W, H), (2, 4, 14))
    return Image.composite(black, img, mask)


def cells_layer(masks, rng):
    cells = place_cells(masks, rng)
    layer = Image.new("RGB", (W * SS, H * SS), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    cells.sort(key=lambda c: -c[2])                    # besar dulu, kecil di atas
    for x, y, r, reg in cells:
        draw_cell(d, x, y, r, cell_color(x, y, reg, rng), rng)
    layer = layer.resize((W, H), Image.LANCZOS)
    # urat sayap: garis tipis memancar dari tubuh
    vein = Image.new("RGB", (W, H), (0, 0, 0))
    vd = ImageDraw.Draw(vein)
    for side in (1, -1):
        for ang, ln, y0 in ((-58, 700, -120), (-42, 780, -100), (-26, 760, -80), (-10, 700, -50),
                            (14, 520, 10), (32, 470, 40), (50, 400, 70)):
            a = math.radians(ang)
            x0, y0_ = CX + side * 30, CY + y0
            x1, y1 = x0 + side * ln * math.cos(a), y0_ + ln * math.sin(a)
            vd.line([(x0, y0_), (x1, y1)], fill=(255, 255, 255), width=3)
    vein = vein.filter(ImageFilter.GaussianBlur(1.2))
    vein = ImageEnhance.Brightness(vein).enhance(0.28)
    layer = ImageChops.screen(layer, vein)
    # antena
    ant = ImageDraw.Draw(layer)
    for side in (1, -1):
        pts = [(CX + side * 14, CY - 318)]
        for k in range(1, 40):
            t = k / 39
            pts.append((CX + side * (14 + 150 * t - 40 * t * t), CY - 318 - 330 * t + 70 * t * t))
        ant.line(pts, fill=(255, 224, 140), width=5)
        ex, ey = pts[-1]
        ant.ellipse([ex - 14, ey - 14, ex + 14, ey + 14], fill=(255, 140, 70))
        ant.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill=(255, 245, 200))
    return layer


def glow(layer):
    out = layer
    for rad, gain in ((8, 0.14), (26, 0.20), (70, 0.22)):
        b = layer.filter(ImageFilter.GaussianBlur(rad))
        b = ImageEnhance.Brightness(b).enhance(gain * 2)
        out = ImageChops.screen(out, b)
    return out


def sparkle(img, rng):
    """Titik terang kecil: debu sel dan butir pendar."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    cols = [(255, 90, 180), (60, 210, 255), (255, 200, 80), (130, 255, 150), (160, 140, 255)]
    for _ in range(420):
        x, y = rng.randrange(W), rng.randrange(H)
        r = rng.choice((1, 1, 2, 2, 3, 4))
        c = rng.choice(cols)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    layer = ImageChops.screen(layer, layer.filter(ImageFilter.GaussianBlur(5)))
    layer = ImageEnhance.Brightness(layer).enhance(0.7)
    return ImageChops.screen(img, layer)


def grain(img):
    noise = Image.effect_noise((W, H), 38).convert("RGB")
    noise = ImageEnhance.Brightness(noise).enhance(0.9)
    noise = ImageEnhance.Contrast(noise).enhance(0.35)
    return ImageChops.add(img, noise, scale=1.0, offset=-128 + 6)


def text_layer(title_lines, author, subtitle="SEBUAH NOVEL"):
    """Teks digambar pada lapisan hitam agar bisa diberi pendar halus."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)

    def centered(txt, y, f, fill, track=0):
        if track:
            widths = [d.textlength(ch, font=f) for ch in txt]
            total = sum(widths) + track * (len(txt) - 1)
            x = (W - total) / 2
            for ch, w in zip(txt, widths):
                d.text((x, y), ch, font=f, fill=fill)
                x += w + track
        else:
            d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=fill)

    cream = (250, 240, 218)
    centered(subtitle, 128, font("LinLibertine_R.otf", 46), (206, 196, 230), track=14)
    y = 215
    for txt, size in title_lines:
        f = font("LinLibertine_RI.otf", size)
        centered(txt, y, f, cream)
        y += int(size * 1.02)
    centered(author.upper(), H - 235, font("LinLibertine_R.otf", 76), (255, 226, 160), track=22)
    return layer


def science_marks():
    """Penanda ala mikrograf: batang skala, bidik silang, keterangan."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = (225, 225, 240)
    # batang skala 20 µm (kiri bawah gambar)
    y = 2050
    x0, x1 = 150, 150 + 220
    d.line([(x0, y), (x1, y)], fill=ink, width=6)
    d.line([(x0, y - 14), (x0, y + 14)], fill=ink, width=4)
    d.line([(x1, y - 14), (x1, y + 14)], fill=ink, width=4)
    fs = font("LinBiolinum_R.otf", 40)
    d.text((x0, y + 22), "20 µm", font=fs, fill=ink)
    # keterangan kanan bawah
    fc = font("LinBiolinum_R.otf", 34)
    lines = ["imunofluoresensi · ×630", "DAPI · FITC · TRITC"]
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=fc)
        d.text((W - 150 - w, y - 20 + i * 46), ln, font=fc, fill=(190, 190, 215))
    # penanda sudut tipis
    for (ax, ay, sx, sy) in ((90, 90, 1, 1), (W - 90, 90, -1, 1), (90, H - 90, 1, -1), (W - 90, H - 90, -1, -1)):
        d.line([(ax, ay), (ax + sx * 70, ay)], fill=(200, 175, 110), width=3)
        d.line([(ax, ay), (ax, ay + sy * 70)], fill=(200, 175, 110), width=3)
    # tanda ukur di sisi gambar
    for k in range(-6, 7):
        yy = CY + k * 100
        ln = 22 if k % 2 == 0 else 12
        d.line([(100, yy), (100 + ln, yy)], fill=(120, 120, 160), width=2)
        d.line([(W - 100, yy), (W - 100 - ln, yy)], fill=(120, 120, 160), width=2)
    return layer


def make_cover(title_lines, author, path):
    rng = random.Random(2002)                  # tahun lahir tokoh
    img = background(rng)
    masks = make_masks()
    lay = cells_layer(masks, rng)
    img = ImageChops.screen(img, glow(lay))
    img = ImageChops.screen(img, lay)
    img = sparkle(img, rng)
    img = vignette(img)
    txt = text_layer(title_lines, author)
    soft = ImageEnhance.Brightness(txt.filter(ImageFilter.GaussianBlur(14))).enhance(1.2)
    img = ImageChops.screen(img, soft)
    img = ImageChops.screen(img, txt)
    img = ImageChops.screen(img, science_marks())
    img = grain(img)
    path = Path(path)
    if path.suffix.lower() in (".jpg", ".jpeg"):
        img.save(path, quality=92, optimize=True, subsampling=0)
    else:
        img.save(path)
    return path


if __name__ == "__main__":
    spec = sys.argv[1].split("|")
    sizes = [220, 120, 220]
    lines = list(zip(spec, sizes))
    make_cover(lines, sys.argv[2], sys.argv[3])

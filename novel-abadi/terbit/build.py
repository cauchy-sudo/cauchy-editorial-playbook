#!/usr/bin/env python3
"""Kompilasi naskah novel menjadi PDF (XeLaTeX) dan EPUB.

Pemakaian:
    python3 build.py                       # PDF + EPUB
    python3 build.py --only pdf            # hanya PDF
    python3 build.py --title "Judul" --author "Nama Penulis"

Prasyarat: pandoc, xelatex (TeX Live), font Linux Libertine O, Pillow (untuk sampul).
Sumber: ../prolog.md, ../bab-NN.md, ../interlude-N.md, ../epilog.md
Keluaran: terbit/<slug>.pdf, terbit/<slug>.epub (+ berkas .tex untuk diperiksa)
"""
import argparse, re, subprocess, sys, shutil, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
BUILD = HERE / "_build"

DEFAULT_TITLE = "Usia yang Tidak Dihitung"      # judul kerja
DEFAULT_SUBTITLE = "Sebuah novel"
DEFAULT_AUTHOR = "Nama Penulis"                  # ganti sebelum terbit

# ---------------------------------------------------------------- struktur
PARTS = [
    (1,  "I",   "Kupu-kupu di Pipi", "2013–2017"),
    (10, "II",  "Tangga",            "2017–2025"),
    (27, "III", "Formula",           "2026–2031"),
]
INTERLUDES_AFTER = {7: "interlude-1.md", 18: "interlude-2.md", 26: "interlude-3.md"}


def sequence():
    """Urutan unit baca: ('part', roman, title, years) atau ('file', Path)."""
    seq = [("file", SRC / "prolog.md")]
    for n in range(1, 38):
        for start, roman, ttl, yrs in PARTS:
            if n == start:
                seq.append(("part", roman, ttl, yrs))
        seq.append(("file", SRC / f"bab-{n:02d}.md"))
        if n in INTERLUDES_AFTER:
            seq.append(("file", SRC / INTERLUDES_AFTER[n]))
    seq.append(("file", SRC / "epilog.md"))
    return seq


def parse_file(path: Path):
    """Pisahkan judul dan isi. Kembalikan dict(kind, num, title, sub, body)."""
    text = path.read_text(encoding="utf-8").strip("\n")
    first, _, rest = text.partition("\n")
    head = first.lstrip("#").strip()
    body = rest.strip("\n")
    m = re.match(r"Bab (\d+)\s+—\s+(.*)$", head)
    if m:
        return dict(kind="chapter", num=int(m.group(1)), title=m.group(2).strip(), sub=None, body=body)
    m = re.match(r"(.+?)\s+—\s+(.*)$", head)
    if m:
        kind = "interlude" if m.group(1).startswith("Interlude") else "special"
        return dict(kind=kind, num=None, title=m.group(1).strip(), sub=m.group(2).strip(), body=body)
    raise ValueError(f"Judul tak dikenali di {path}: {head!r}")


SCENE = "SCENEBREAKPLACEHOLDER"


def mark_scene_breaks(body: str, placeholder: str) -> str:
    # beri baris kosong di sekeliling agar pandoc memperlakukannya sebagai paragraf sendiri
    return re.sub(r"(?m)^[ \t]*---[ \t]*$", "\n" + placeholder + "\n", body)


def pandoc_md_to(body: str, fmt: str) -> str:
    r = subprocess.run(
        ["pandoc", "-f", "markdown+smart-yaml_metadata_block", "-t", fmt, "--wrap=none"],
        input=body, capture_output=True, text=True, check=True)
    return r.stdout


# --------------------------------------------------------------------- PDF
def tex_escape(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(rep.get(c, c) for c in s)


PREAMBLE = r"""
\documentclass[11pt,twoside,openany]{book}
\usepackage[paperwidth=14cm,paperheight=21cm,inner=21mm,outer=17mm,top=21mm,bottom=24mm]{geometry}
\usepackage{fontspec}
\setmainfont{LinLibertine_R.otf}[
  Path=/usr/share/fonts/opentype/linux-libertine/,
  BoldFont=LinLibertine_RB.otf, ItalicFont=LinLibertine_RI.otf, BoldItalicFont=LinLibertine_RBI.otf,
  Ligatures=TeX]
\usepackage[indonesian]{babel}
\addto\captionsindonesian{%
  \renewcommand{\chaptername}{Bab}%
  \renewcommand{\partname}{Babak}%
  \renewcommand{\contentsname}{Daftar Isi}}
\usepackage{microtype}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{etoolbox}
\linespread{1.07}
\setlength{\parindent}{1.25em}
\setlength{\parskip}{0pt}
\emergencystretch=2em
\clubpenalty=10000
\widowpenalty=10000
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

% --- judul bab / babak
\titleformat{\chapter}[display]{\centering\normalfont}
  {\small\textsc{\chaptertitlename}\ \thechapter}{0.7em}{\Large\itshape}
\titleformat{name=\chapter,numberless}[display]{\centering\normalfont}{}{0pt}{\Large\itshape}
\titlespacing*{\chapter}{0pt}{14mm}{13mm}
\titleformat{\part}[display]{\centering\normalfont}
  {\small\textsc{\partname}\ \thepart}{0.9em}{\huge\itshape}
\renewcommand{\thepart}{\Roman{part}}

% --- penanda adegan
\makeatletter
\newcommand{\scenebreak}{\par\vspace{0.9em}{\centering\textsc{*\hspace{0.7em}*\hspace{0.7em}*}\par}\vspace{0.9em}\@afterindentfalse\@afterheading}
\makeatother

% --- kepala/kaki halaman
\pagestyle{fancy}
\fancyhf{}
\fancyhead[CE]{\small\textsc{\booktitleshort}}
\fancyhead[CO]{\small\itshape\leftmark}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\thepage}\renewcommand{\headrulewidth}{0pt}}
\renewcommand{\chaptermark}[1]{\markboth{#1}{}}
\renewcommand{\partmark}[1]{\markboth{}{}}

\setcounter{tocdepth}{0}
\usepackage[hidelinks,unicode,bookmarks=true,bookmarksopen=false,
  pdftitle={\booktitleplain},pdfauthor={\bookauthorplain},pdflang={id}]{hyperref}
"""


def build_pdf(title, subtitle, author, slug):
    BUILD.mkdir(exist_ok=True)
    out = []
    out.append(PREAMBLE.replace(r"\booktitleshort", tex_escape(title)))
    # makro metadata untuk hyperref (harus didefinisikan sebelum \usepackage{hyperref})
    pre = "\n".join(out)
    pre = pre.replace(r"\documentclass[11pt,twoside,openany]{book}",
                      r"\documentclass[11pt,twoside,openany]{book}" "\n"
                      + r"\newcommand{\booktitleplain}{" + tex_escape(title) + "}\n"
                      + r"\newcommand{\bookauthorplain}{" + tex_escape(author) + "}\n", 1)
    out = [pre]
    out.append(r"\begin{document}")
    # halaman judul
    out.append(r"""
\frontmatter
\pagestyle{empty}
\begin{titlepage}
\centering
\vspace*{26mm}
{\small\textsc{""" + tex_escape(subtitle) + r"""}\par}
\vspace{10mm}
{\fontsize{30}{34}\selectfont\itshape """ + tex_escape(title) + r"""\par}
\vspace{10mm}
{\small\textsc{*\hspace{0.7em}*\hspace{0.7em}*}\par}
\vfill
{\large """ + tex_escape(author) + r"""\par}
\vspace{8mm}
{\footnotesize\textsc{Draf 1}\par}
\vspace{14mm}
\end{titlepage}
\cleardoublepage
\thispagestyle{empty}
\vspace*{\fill}
\begin{center}\footnotesize
\begin{minipage}{0.82\textwidth}\raggedright\setlength{\parindent}{0pt}\setlength{\parskip}{0.6em}
\textsc{Draf 1 — belum disunting.}

Novel ini adalah karya fiksi. Tokoh, peristiwa, dan lembaga tertentu (termasuk
Institut Hartwell, Halcyon Longevity Fund, dan Kestrel Biotherapeutics) adalah rekaan.
Latar kebijakan dan peristiwa nyata, seperti JKN, KIP Kuliah, dan pandemi COVID-19,
dipakai sebagai latar; rinciannya belum diverifikasi.

Bagian medis, ilmiah, hukum, dan budaya harus diperiksa para ahli sebelum naskah diterbitkan.
Naskah ini sengaja tidak memuat petunjuk teknis apa pun tentang pembuatan atau
pemberian formula yang diceritakan.
\end{minipage}
\end{center}
\vspace*{\fill}
\clearpage
\pagestyle{fancy}
\tableofcontents
\mainmatter
""")
    for item in sequence():
        if item[0] == "part":
            _, roman, ptitle, years = item
            out.append(r"\part[" + tex_escape(ptitle) + r"]{" + tex_escape(ptitle) + r"\\[0.7em]\normalsize\upshape " + tex_escape(years.replace("–", "--")) + "}")
            continue
        info = parse_file(item[1])
        body = mark_scene_breaks(info["body"], SCENE)
        tex = pandoc_md_to(body, "latex")
        tex = re.sub(r"(?m)^" + SCENE + r"\s*$", r"\\scenebreak", tex)
        if info["kind"] == "chapter":
            out.append(r"\chapter{" + tex_escape(info["title"]) + "}")
        else:
            t, s = tex_escape(info["title"]), tex_escape(info["sub"])
            full = f"{t} — {s}"
            out.append(r"\chapter*{" + t + r"\\[0.5em]\normalsize\upshape " + s + "}")
            out.append(r"\addcontentsline{toc}{chapter}{" + full + "}")
            out.append(r"\markboth{" + t + r"}{}")
        out.append(tex.strip() + "\n")
    out.append(r"\end{document}")
    tex_path = BUILD / f"{slug}.tex"
    tex_path.write_text("\n".join(out), encoding="utf-8")
    for _ in range(3):  # tiga putaran: daftar isi + penanda
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                           cwd=BUILD, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-3000:])
            sys.exit("xelatex gagal")
    log = (BUILD / f"{slug}.log").read_text(encoding="utf-8", errors="replace")
    missing = re.findall(r"Missing character:.*", log)
    overfull = re.findall(r"Overfull \\hbox \(([\d.]+)pt", log)
    bad = [x for x in overfull if float(x) > 8]
    print(f"[pdf] karakter hilang: {len(missing)}; overfull>8pt: {len(bad)}")
    shutil.copy(BUILD / f"{slug}.pdf", HERE / f"{slug}.pdf")
    shutil.copy(tex_path, HERE / f"{slug}.tex")
    return HERE / f"{slug}.pdf"


# -------------------------------------------------------------------- EPUB
CSS = """\
@charset "utf-8";
body { font-family: serif; line-height: 1.5; margin: 0 0.4em; text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
p { margin: 0; text-indent: 1.35em; orphans: 2; widows: 2; }
h1, h2 { text-align: center; font-weight: normal; font-style: italic; line-height: 1.25; margin: 3.2em 0 1.8em 0; page-break-before: always; page-break-after: avoid; }
h1 { font-size: 1.7em; }
h2 { font-size: 1.45em; }
h1.part { font-size: 1.9em; margin-top: 8em; }
h2 .bab-no, h1.part .part-no { display: block; font-style: normal; font-size: 0.5em; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.7em; }
h2 .sep { display: none; }
h1.part .part-years { display: block; font-style: normal; font-size: 0.45em; letter-spacing: 0.15em; margin-top: 0.9em; }
div.sub { text-align: center; font-style: italic; font-size: 0.9em; margin: -1.2em 0 2em 0; }
div.sub p { text-indent: 0; }
h1 + p, h2 + p, div.sub + p, div.scenebreak + p { text-indent: 0; }
div.scenebreak { text-align: center; margin: 1.1em 0; letter-spacing: 0.5em; }
div.scenebreak p { text-indent: 0; }
nav#toc ol { list-style: none; padding-left: 0.4em; }
nav#toc ol ol { padding-left: 1.2em; }
section.titlepage, div.titlepage { text-align: center; }
"""


def make_cover(title, subtitle, author, path: Path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[epub] Pillow tidak ada; sampul dilewati")
        return None
    W, H = 1600, 2400
    img = Image.new("RGB", (W, H), (18, 32, 48))
    d = ImageDraw.Draw(img)
    # gradien vertikal
    top, bot = (16, 30, 46), (46, 40, 58)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    # bulan (lingkaran pucat) + cincin sel
    cx, cy, r = W // 2, 1400, 360
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(231, 222, 200))
    d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], outline=(120, 108, 92), width=6)
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(120, 108, 92))
    for k, rr in enumerate((440, 520, 600)):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(150 - 25 * k, 140 - 22 * k, 130 - 20 * k), width=3)
    fd = "/usr/share/fonts/opentype/linux-libertine/"
    f_it = ImageFont.truetype(fd + "LinLibertine_RI.otf", 150)
    f_sm = ImageFont.truetype(fd + "LinLibertine_R.otf", 56)
    f_au = ImageFont.truetype(fd + "LinLibertine_R.otf", 84)

    def centered(text, y, font, fill, spacing=0):
        # perataan tengah dengan wrap sederhana
        words, lines, cur = text.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=font) > W - 240 and cur:
                lines.append(cur); cur = w
            else:
                cur = test
        lines.append(cur)
        for ln in lines:
            d.text(((W - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=fill)
            y += int(font.size * 1.18)
        return y
    centered(subtitle.upper(), 170, f_sm, (200, 190, 170))
    centered(title, 300, f_it, (240, 232, 214))
    centered(author, H - 270, f_au, (225, 216, 196))
    img.save(path)
    return path


def build_epub(title, subtitle, author, slug):
    BUILD.mkdir(exist_ok=True)
    md = []
    for item in sequence():
        if item[0] == "part":
            _, roman, ptitle, years = item
            md.append(f'# [Babak {roman}]{{.part-no}}[. ]{{.sep}}{ptitle}[{years}]{{.part-years}} {{.part}}\n')
            continue
        info = parse_file(item[1])
        body = mark_scene_breaks(info["body"], "\n::: scenebreak\n\\* \\* \\*\n:::\n")
        if info["kind"] == "chapter":
            md.append(f'## [Bab {info["num"]}]{{.bab-no}}[. ]{{.sep}}{info["title"]}\n')
        elif info["kind"] == "interlude":
            md.append(f'## {info["title"]}\n\n::: sub\n{info["sub"]}\n:::\n')
        else:
            md.append(f'# {info["title"]}\n\n::: sub\n{info["sub"]}\n:::\n')
        md.append(body + "\n")
    (BUILD / "epub.md").write_text("\n".join(md), encoding="utf-8")
    (BUILD / "epub.css").write_text(CSS, encoding="utf-8")
    meta = (BUILD / "epub-meta.yaml")
    meta.write_text(
        f"---\ntitle: \"{title}\"\nsubtitle: \"{subtitle}\"\nauthor: \"{author}\"\nlang: id\n"
        "rights: \"Draf 1 — belum disunting. Karya fiksi.\"\n"
        "description: \"Draf pertama novel tentang seorang anak desa di Gunungkidul, penyakit autoimun, dan sains peremajaan sel.\"\n"
        "toc-title: \"Daftar Isi\"\n---\n", encoding="utf-8")
    cmd = ["pandoc", "-f", "markdown+smart+fenced_divs+bracketed_spans+header_attributes", "-t", "epub3",
           "--metadata-file", str(meta), "--css", str(BUILD / "epub.css"),
           "--toc", "--toc-depth=2", "--split-level=2", "--wrap=none",
           "-o", str(HERE / f"{slug}.epub"), str(BUILD / "epub.md")]
    cover = make_cover(title, subtitle, author, BUILD / "cover.png")
    if cover:
        cmd[1:1] = ["--epub-cover-image", str(cover)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("pandoc epub gagal:\n" + r.stderr)
    if r.stderr.strip():
        print("[epub] peringatan pandoc:", r.stderr.strip()[:500])
    # pemeriksaan sederhana: semua XHTML terbaca sebagai XML
    import xml.dom.minidom as mx
    with zipfile.ZipFile(HERE / f"{slug}.epub") as z:
        n = 0
        for name in z.namelist():
            if name.endswith((".xhtml", ".opf", ".ncx")):
                mx.parseString(z.read(name)); n += 1
    print(f"[epub] {n} berkas XML tervalidasi sintaks")
    return HERE / f"{slug}.epub"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", default=DEFAULT_TITLE)
    ap.add_argument("--subtitle", default=DEFAULT_SUBTITLE)
    ap.add_argument("--author", default=DEFAULT_AUTHOR)
    ap.add_argument("--slug", default="usia-yang-tidak-dihitung")
    ap.add_argument("--only", choices=["pdf", "epub"])
    a = ap.parse_args()
    if a.only != "epub":
        print("[pdf] ->", build_pdf(a.title, a.subtitle, a.author, a.slug))
    if a.only != "pdf":
        print("[epub] ->", build_epub(a.title, a.subtitle, a.author, a.slug))


if __name__ == "__main__":
    main()

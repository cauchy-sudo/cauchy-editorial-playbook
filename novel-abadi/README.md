# Novel Peremajaan Sel — Draf 1 Lengkap

Judul kerja belum ditetapkan (usulan: *Usia yang Tidak Dihitung*, *Sel yang Mengingat Muda*, *Jam Biologis*).
Sudut pandang orang pertama (Wulan). Sekitar 64.000 kata: prolog, 37 bab, 3 interlude, epilog.

## Urutan baca
| Berkas | Isi | Tahun |
|---|---|---|
| `prolog.md` | Tangan Ibu | 2031 |
| `bab-01.md` … `bab-09.md` | Babak I: kupu-kupu di pipi, diagnosis lupus, SMP | 2013–2017 |
| `interlude-1.md` | Menolak difoto; alarm "Kontrol" (muncul setelah bab 7) | 2031 |
| `bab-10.md` … `bab-18.md` | Babak II-A: SMA, olimpiade, Naufal, kambuh, pandemi, KIP Kuliah | 2017–2020 |
| `interlude-2.md` | Merekam suara Ibu; Sekar (setelah bab 18) | 2031 |
| `bab-19.md` … `bab-26.md` | Babak II-B: lab, titik tengah, Bayu, AI, publikasi, beasiswa, Inggris | 2020–2025 |
| `interlude-3.md` | Pesan Rizal yang tak dibalas (setelah bab 26) | 2031 |
| `bab-27.md` … `bab-37.md` | Babak III: gagasan, Lumen, tikus, kambuh, dosis pertama, ingatan, rilis terbuka, Rasulan, laut | 2026–2031 |
| `epilog.md` | Arsip | 2031 |

**Versi satu berkas:** `naskah-lengkap.md` (semua bagian berurutan, dengan daftar isi).

## Dokumen kerja
- `07-ledger-dan-verifikasi.md` — **mulai di sini** untuk kontinuitas, daftar verifikasi fakta, dan kelemahan yang diketahui.
- `00-konsep.md`, `01-tokoh-dan-dunia.md`, `02-panduan-suara.md`, `03-outline.md`, `04-adat-budaya.md`, `05-struktur-dan-daya-tarik.md`, `06-celah-logika.md`, `panduan-penulisan.md` — dokumen perencanaan (sebagian sudah digantikan oleh draf; lihat ledger).

## Terbitan (PDF dan EPUB)
Folder `terbit/` berisi hasil kompilasi dan skrip pembuatnya.
| Berkas | Keterangan |
|---|---|
| `terbit/usia-yang-tidak-dihitung.pdf` | PDF XeLaTeX, 14 × 21 cm, font Linux Libertine, ±333 halaman, daftar isi dan penanda bacaan |
| `terbit/usia-yang-tidak-dihitung.epub` | EPUB 3 dengan sampul; lolos EpubCheck (0 galat, 0 peringatan) |
| `terbit/usia-yang-tidak-dihitung.tex` | sumber LaTeX hasil pembangkitan (untuk diperiksa atau disunting) |
| `terbit/build.py` | skrip build ulang |

Bangun ulang setelah merevisi naskah:
```
python3 terbit/build.py                                   # PDF + EPUB
python3 terbit/build.py --title "Judul" --author "Nama"   # ganti judul dan penulis
python3 terbit/build.py --only pdf                        # atau --only epub
```
Prasyarat: `pandoc`, TeX Live (`xelatex`), font Linux Libertine O, `Pillow` (sampul), opsional `epubcheck`.
**Judul dan nama penulis masih placeholder**: "Usia yang Tidak Dihitung" (judul kerja) dan "Nama Penulis".

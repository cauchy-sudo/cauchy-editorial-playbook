# Cauchy Editorial Playbook

Situs statis panduan editor, reviewer, copyeditor, dan layout editor.

- Panduan utama: `index.html`
- Galeri visualisasi: `visualisasi.html` (24 entri; 13 PDF berlisensi terbuka disimpan di `papers/`)
- Data kurasi, versi, dan pertanyaan review: `visualisasi-data.json`
- Atribusi, lisensi per paper, dan checksum: `SOURCES-VISUALISASI.md`

Galeri memakai CSS/JavaScript lokal tanpa CDN atau layanan penyimpanan lain. PDF disalin tanpa modifikasi dari berkas sumber; thumbnail adalah rasterisasi yang dipotong di sekitar figure, sedangkan dialog menampilkan halaman lengkap. Paper lain diakses melalui tautan penerbit, penulis, atau arXiv. Jurnal pada katalog bukan sertifikasi peringkat atau jaminan kebenaran ilmiah.

## Pemeliharaan

`scripts/build_visual_gallery.py` memuat kurasi dan membangun JSON, catatan sumber, serta gambar WebP. Skrip memakai Python dan `pypdfium2`; direktori sumber dapat diatur lewat argumen `--source`. Setelah menambah paper, pastikan DOI, versi, halaman figure, kredit pihak ketiga, dan lisensi sudah diperiksa.

Untuk pengujian lokal: `python3 -m http.server 8765`. `scripts/test_gallery.cjs` memeriksa galeri di browser melalui Playwright (memerlukan Chrome dan Playwright lokal); tidak menjadi dependensi situs terbit.

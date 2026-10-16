"""Build the static gallery from an audited source directory (PDFs stay unmodified)."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]

# id, title, authors, journal, publisher, journal year, DOI, category,
# selected figure, PDF page, lesson, review question, version note, mirror license
ROWS = [
 (1,'Highly accurate protein structure prediction with AlphaFold','Jumper et al.','Nature','Nature Portfolio',2021,'10.1038/s41586-021-03819-2','Benchmark','Fig. 1',2,'Benchmark, alur metode, dan contoh hasil dibedakan menjadi panel dengan fungsi yang jelas.','Apakah metrik, jumlah sampel, dan baseline memungkinkan perbandingan yang adil?','Versi penerbit.','CC BY 4.0'),
 (2,'Accurate structure prediction of biomolecular interactions with AlphaFold 3','Abramson et al.','Nature','Nature Portfolio',2024,'10.1038/s41586-024-07487-w','Benchmark','Fig. 1',2,'Ringkasan hasil memadukan contoh struktur dan perbandingan kuantitatif dalam satu susunan panel.','Apakah warna dan legenda tetap konsisten ketika jenis objek berubah antarpanel?','Versi penerbit; perhatikan catatan koreksi pada sumber resmi.','CC BY 4.0'),
 (3,'Highly accurate protein structure prediction for the human proteome','Tunyasuvunakool et al.','Nature','Nature Portfolio',2021,'10.1038/s41586-021-03828-1','Ketidakpastian','Fig. 1',2,'Distribusi confidence dan cakupan data menjelaskan batas hasil, bukan hanya menampilkan contoh yang berhasil.','Apakah confidence dibedakan dari akurasi terukur dan apakah distribusi lengkap terlihat?','Versi penerbit.','CC BY 4.0'),
 (4,'Array programming with NumPy','Harris et al.','Nature','Nature Portfolio',2020,'10.1038/s41586-020-2649-2','Diagram metode','Fig. 1',2,'Array, indeks, dan operasi dijelaskan dengan contoh visual konkret sebelum pembahasan abstrak.','Apakah pembaca dapat mengikuti perpindahan data tanpa menebak arti warna atau panah?','Versi penerbit.','CC BY 4.0'),
 (5,'Scaling deep learning for materials discovery','Merchant et al.','Nature','Nature Portfolio',2023,'10.1038/s41586-023-06735-9','Benchmark','Fig. 1',2,'Diagram alur penemuan dan hasil kuantitatif menautkan proses komputasi dengan bukti kontribusinya.','Apakah jumlah kandidat, hasil validasi, dan dasar perbandingan dinyatakan terpisah?','Versi penerbit.','CC BY 4.0'),
 (6,'Large language models encode clinical knowledge','Singhal et al.','Nature','Nature Portfolio',2023,'10.1038/s41586-023-06291-2','Benchmark','Fig. 2',3,'Perbandingan pada beberapa dataset memakai susunan panel agar variasi performa tetap terlihat.','Apakah jenis evaluasi, baseline, serta arti error bar dijelaskan, tanpa menyamakan skor ujian dengan kelayakan klinis?','Versi penerbit; contoh ini menilai penyajian data, bukan memberi rekomendasi klinis.','CC BY 4.0'),
 (7,'A pneumonia outbreak associated with a new coronavirus of probable bat origin','Zhou et al.','Nature','Nature Portfolio',2020,'10.1038/s41586-020-2012-7','Multipanel','Susunan panel dan caption',None,'Baca susunan panel dan cara caption menghubungkan beberapa bentuk bukti; batasi penilaian pada komunikasi visual.','Apakah tiap panel punya pesan dan legenda sendiri, serta apakah klaim keseluruhan melampaui bukti yang ditampilkan?','Rujukan konteks melalui penerbit. Status koreksi dan catatan editorial mengikuti sumber resmi.',None),
 (8,'The misuse of colour in science communication','Crameri, Shephard & Heron','Nature Communications','Nature Portfolio',2020,'10.1038/s41467-020-19160-7','Warna & aksesibilitas','Pembahasan colour map',6,'Pilihan colour map merupakan keputusan ilmiah: gradien warna dapat memperjelas atau mendistorsi variasi data.','Apakah skala warna memiliki urutan yang masuk akal, tetap terbaca dalam greyscale, dan ramah gangguan penglihatan warna?','Versi penerbit. Gunakan bersama caption dan pembahasan warna.','CC BY 4.0'),
 (9,'Quantum supremacy using a programmable superconducting processor','Arute et al.','Nature','Nature Portfolio',2019,'10.1038/s41586-019-1666-5','Benchmark','Fig. 4',5,'Panel benchmark menyandingkan hasil pengukuran dan pembandingan komputasi; skala dan cara estimasi harus dibaca bersama.','Apakah hasil terukur dibedakan dari ekstrapolasi, dan apakah skala logaritmik dijelaskan?','PDF lokal tidak menyatakan lisensi redistribusi terbuka; baca dari sumber resmi.',None),
 (10,'Ten Simple Rules for Better Figures','Rougier, Droettboom & Bourne','PLOS Computational Biology','PLOS',2014,'10.1371/journal.pcbi.1003833','Prinsip visual','Figure 3',4,'Data yang sama perlu penataan berbeda untuk artikel dan presentasi; ukuran label serta kepadatan harus mengikuti media.','Apakah figure masih terbaca pada ukuran cetak akhir, dan apakah pesan utama dapat ditemukan tanpa membaca seluruh artikel?','Versi penerbit; artikel menyatakan CC0.','CC0 1.0'),
 (11,'Safe and just Earth system boundaries','Rockström et al.','Nature','Nature Portfolio',2023,'10.1038/s41586-023-06083-8','Peta & spasial','Fig. 1',3,'Diagram radial merangkum banyak dimensi dengan batas rujukan dan pengodean kategori yang dijelaskan dalam caption.','Apakah normalisasi setiap sumbu dan arti batas dijelaskan sehingga panjang radial tidak disalahartikan sebagai satuan asli?','Versi penerbit. Diagram radial perlu dibaca kritis, bukan ditiru untuk semua dataset.','CC BY 4.0'),
 (12,'Accurate medium-range global weather forecasting with 3D neural networks','Bi et al.','Nature','Nature Portfolio',2023,'10.1038/s41586-023-06185-3','Peta & spasial','Fig. 3 dan Fig. 4',4,'Small multiples menempatkan prediksi, pembanding, dan referensi pada tata letak spasial yang bisa dibandingkan langsung.','Apakah waktu, area, skala warna, dan satuan sama untuk semua metode yang dibandingkan?','Versi penerbit.','CC BY 4.0'),
 (13,'SciPy 1.0: fundamental algorithms for scientific computing in Python','Virtanen et al.','Nature Methods','Nature Portfolio',2020,'10.1038/s41592-019-0686-2','Benchmark','Fig. 3',8,'Benchmark menampilkan perubahan kinerja antarversi sehingga perkembangan perangkat lunak dapat dinilai secara kuantitatif.','Apakah lingkungan komputasi, versi, ukuran masalah, dan arah metrik dijelaskan agar peningkatan kinerja dapat ditafsirkan?','Versi penerbit.','CC BY 4.0'),
 (14,'Beyond Bar and Line Graphs: Time for a New Data Presentation Paradigm','Weissgerber et al.','PLOS Biology','PLOS',2015,'10.1371/journal.pbio.1002128','Distribusi data','Fig. 1',2,'Beberapa distribusi berbeda dapat menghasilkan ringkasan bar graph yang hampir sama; titik individual membuka informasi yang hilang.','Apakah grafik menunjukkan distribusi, outlier, jumlah sampel, dan struktur berpasangan bila relevan?','Versi penerbit.','CC BY 4.0'),
 (15,'A new coronavirus associated with human respiratory disease in China','Wu et al.','Nature','Nature Portfolio',2020,'10.1038/s41586-020-2008-3','Multipanel','Fig. 2',3,'Susunan panel pohon memperlihatkan bagaimana label, legenda, dan konsistensi tata letak membantu membaca perbandingan yang kompleks.','Apakah arti panjang cabang, dukungan statistik, dan perbedaan antarpanel dijelaskan sebelum pembaca menarik kesimpulan?','Rujukan konteks melalui penerbit; pembahasan galeri dibatasi pada penyajian visual.',None),
 (16,'Physics Informed Deep Learning (Part I): Data-driven Solutions of Nonlinear Partial Differential Equations','Raissi, Perdikaris & Karniadakis','Journal of Computational Physics','Elsevier',2019,'10.1016/j.jcp.2018.10.045','Validasi model','Figure 1 pada preprint',8,'Heatmap solusi disandingkan dengan irisan kurva sehingga kecocokan lokal tidak tersembunyi di balik satu skor agregat.','Apakah prediksi dan referensi memakai sumbu yang sama dan lokasi observasi dibedakan dari titik evaluasi?','Penting: PDF sumber sebenarnya preprint arXiv:1711.10561v1 (2017), bukan artikel JCP 2019. DOI menunjuk artikel jurnal terkait.',None),
 (17,'Graph neural networks: A review of methods and applications','Zhou et al.','AI Open','Elsevier',2020,'10.1016/j.aiopen.2021.01.001','Diagram metode','Fig. 3',5,'Diagram modul menyajikan perbedaan mekanisme secara berdampingan dengan notasi dan bentuk visual yang teratur.','Apakah panel membandingkan operasi yang setara dan apakah simbol yang berulang selalu memiliki arti yang sama?','Volume jurnal 2020; DOI memuat 2021. Tahun mengikuti volume artikel.','CC BY 4.0'),
 (18,'Deep Learning in Neural Networks: An Overview','Schmidhuber','Neural Networks','Elsevier',2015,'10.1016/j.neunet.2014.09.003','Bacaan pendamping','Tidak ada figure bernomor pada PDF sumber',None,'Gunakan sebagai konteks literatur dan contoh bahwa paper berpengaruh tidak otomatis merupakan teladan visualisasi.','Apakah contoh yang dipilih benar-benar memiliki figure yang mendukung tujuan pelatihan? Jangan memilih hanya berdasarkan reputasi paper.','PDF sumber adalah technical report/arXiv v4 (2014), 88 halaman. Tidak dipromosikan sebagai contoh figure.',None),
 (19,'Community detection in graphs','Fortunato','Physics Reports','Elsevier',2010,'10.1016/j.physrep.2009.11.002','Graf & jaringan','FIG. 2 pada preprint',5,'Warna komunitas dan posisi simpul membantu memperlihatkan struktur jaringan; legenda dan definisi komunitas tetap diperlukan.','Apakah tata letak simpul dibedakan dari hasil algoritma dan apakah warna komunitas konsisten?','PDF sumber arXiv:0906.0612v2. Sejumlah figure memiliki kredit pihak ketiga; tidak disalin ke galeri.',None),
 (20,'Community detection in networks: A user guide','Fortunato & Hric','Physics Reports','Elsevier',2016,'10.1016/j.physrep.2016.09.002','Graf & jaringan','FIG. 4 pada preprint',5,'Skema jaringan sederhana dapat menjelaskan definisi sebelum pembaca menghadapi jaringan nyata yang padat.','Apakah skema konseptual diberi label sebagai ilustrasi, dan apakah kedekatan posisi tidak diklaim sebagai hubungan baru?','PDF sumber arXiv:1608.00163v2; ada figure yang dicetak ulang dengan izin pihak ketiga.',None),
 (21,'A Layered Grammar of Graphics','Wickham','Journal of Computational and Graphical Statistics','Taylor & Francis',2010,'10.1198/jcgs.2009.07098','Prinsip visual','Figure 1–3',4,'Pemisahan data, pemetaan estetika, objek geometris, dan facet memberi bahasa yang presisi untuk mendiskusikan grafik.','Apakah komentar reviewer menunjuk komponen yang perlu diubah, misalnya skala atau pemetaan, alih-alih hanya meminta gambar lebih bagus?','PDF artikel jurnal; izin redistribusi tidak dinyatakan eksplisit pada berkas sumber.',None),
 (22,'Visualizing statistical models: Removing the blindfold','Wickham, Cook & Hofmann','Statistical Analysis and Data Mining','Wiley',2015,'10.1002/sam.11271','Validasi model','Fig. 3–4 pada manuskrip',6,'Model ditampilkan di ruang data agar struktur kelompok dan ketidakpastian dapat diperiksa bersama observasinya.','Apakah visualisasi menampilkan data yang hendak dijelaskan model, bukan hanya kurva atau batas keputusan tanpa konteks?','PDF sumber berupa manuskrip penulis; nomor halaman dapat berbeda dari versi jurnal.',None),
 (23,'Peeking Inside the Black Box: Visualizing Statistical Learning With Plots of Individual Conditional Expectation','Goldstein et al.','Journal of Computational and Graphical Statistics','Taylor & Francis',2015,'10.1080/10618600.2014.907095','Interpretabilitas','Figure 1–2 pada preprint',5,'Kurva individual memperlihatkan heterogenitas hubungan yang dapat hilang pada satu kurva rata-rata.','Apakah efek rata-rata menutupi subkelompok dan apakah banyak kurva masih terbaca tanpa overplotting?','PDF sumber arXiv:1309.6392v2 (2014), bukan versi jurnal 2015.',None),
 (24,'Variational Inference: A Review for Statisticians','Blei, Kucukelbir & McAuliffe','Journal of the American Statistical Association','Taylor & Francis',2017,'10.1080/01621459.2017.1285773','Ketidakpastian','Figure 1 pada preprint',9,'Kontur distribusi menjelaskan perbedaan geometri posterior dan aproksimasi, lebih informatif daripada sekadar nilai objektif.','Apakah orientasi, lebar, dan bentuk kontur membedakan korelasi serta ketidakpastian yang hilang dalam aproksimasi?','PDF sumber arXiv:1601.00670v9 (2018); tahun jurnal 2017. Nomor halaman mengacu preprint.',None),
]

# Thumbnail crops, in fractions of page height. The full page remains available
# in the dialog and the original PDF is never changed.
CROPS = {1:(.05,.51),2:(.05,.60),3:(.04,.53),4:(.06,.39),5:(.05,.58),6:(.05,.34),8:(.04,.88),10:(.04,.48),11:(.06,.51),12:(.04,.94),13:(.08,.33),14:(.43,.89),17:(.05,.68)}


def build(source_directory):
    (ROOT/'papers').mkdir(exist_ok=True)
    (ROOT/'assets/visualisasi').mkdir(parents=True, exist_ok=True)
    items=[]
    for row in ROWS:
        i,title,authors,journal,publisher,year,doi,topic,figure,page,lesson,question,note,license_name=row
        source=next(source_directory.glob(f'{i:02d}_*.pdf'))
        item=dict(id=f'paper-{i:02d}',number=i,title=title,authors=authors,journal=journal,publisher=publisher,year=year,doi=doi,topic=topic,figure=figure,page=page,lesson=lesson,question=question,note=note,sourceFile=source.name)
        item['sourceUrl']='https://doi.org/'+doi
        item['openUrl']={16:'https://arxiv.org/abs/1711.10561',18:'https://arxiv.org/abs/1404.7828',19:'https://arxiv.org/abs/0906.0612',20:'https://arxiv.org/abs/1608.00163',21:'https://vita.had.co.nz/papers/layered-grammar.html',22:'https://vita.had.co.nz/papers/model-vis.html',23:'https://arxiv.org/abs/1309.6392',24:'https://arxiv.org/abs/1601.00670'}.get(i,item['sourceUrl'])
        if license_name:
            # Copy original bytes; never rewrite the scientific article.
            shutil.copy2(source, ROOT/'papers'/source.name)
            item.update(pdf='papers/'+source.name,license=license_name,licenseUrl='https://creativecommons.org/publicdomain/zero/1.0/' if license_name.startswith('CC0') else 'https://creativecommons.org/licenses/by/4.0/',sha256=hashlib.sha256(source.read_bytes()).hexdigest(),bytes=source.stat().st_size)
            doc=pdfium.PdfDocument(source)
            image=doc[page-1].render(scale=1.6).to_pil().convert('RGB')
            image.save(ROOT/f'assets/visualisasi/{i:02d}-page.webp','WEBP',quality=85)
            top,bottom=CROPS[i]
            image.crop((0,int(image.height*top),image.width,int(image.height*bottom))).save(ROOT/f'assets/visualisasi/{i:02d}.webp','WEBP',quality=85)
            item['preview']=f'assets/visualisasi/{i:02d}.webp'
            item['pageImage']=f'assets/visualisasi/{i:02d}-page.webp'
        else:
            item.update(pdf=None,preview=None,license=None)
        items.append(item)
    (ROOT/'visualisasi-data.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
    manifest=['# Sumber dan atribusi galeri visualisasi','', 'Diperiksa 16 Oktober 2026. Galeri merupakan kurasi editorial, bukan peringkat jurnal.','', 'PDF yang disimpan di repositori disalin tanpa modifikasi. Gambar halaman merupakan rasterisasi PDF dengan skala diperkecil; thumbnail dipotong di sekitar area figure, tanpa menyunting data. Dialog menampilkan halaman lengkap termasuk caption. Lisensi materi pihak ketiga, bila ada, tetap mengikuti kredit aslinya. Tautan penerbit tetap menjadi sumber untuk koreksi dan versi terkini.','', 'Nama berkas sumber tidak digunakan sebagai bukti tahun, versi, atau lisensi. Sebagian sumber adalah preprint; perbedaannya dicatat pada setiap entri. Paper tanpa izin distribusi ulang yang jelas hanya ditautkan.','']
    for a in items:
        manifest += [f"## {a['number']:02d}. {a['title']}",f"- Penulis: {a['authors']}; {a['journal']} ({a['year']}).",f"- DOI: {a['sourceUrl']}",f"- Versi: {a['note']}",f"- Fokus: {a['figure']}; halaman PDF sumber: {a['page'] or 'lihat penerbit'}."]
        if a['pdf']:
            manifest += [f"- PDF: [{a['sourceFile']}]({a['pdf']}); {a['bytes']} byte.",f"- Lisensi: [{a['license']}]({a['licenseUrl']}).",f"- SHA-256: `{a['sha256']}`."]
        else:manifest += [f"- Akses: {a['openUrl']}; PDF dan figure tidak disalin ke repositori."]
        manifest += ['']
    (ROOT/'SOURCES-VISUALISASI.md').write_text('\n'.join(manifest))
    print(f'{len(items)} entri; {sum(bool(a["pdf"]) for a in items)} PDF beserta pratinjau disimpan.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True, help='Directory containing the 24 source PDFs')
    build(parser.parse_args().source)

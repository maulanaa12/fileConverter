# Panduan Aplikasi dan Fitur LocalPDF Studio

Dokumen ini menjelaskan identitas aplikasi, kegunaan, setiap menu, pengaturan, contoh penggunaan, hasil keluaran, dan batasan implementasi yang perlu diketahui.

- **Versi yang diperiksa:** v1.2.2.
- **Dasar penjelasan:** pemeriksaan kode aplikasi, template antarmuka, JavaScript, dan modul pemrosesan pada working tree, termasuk perubahan yang belum di-commit saat pemeriksaan.
- **Verifikasi tambahan:** pemeriksaan kode oleh worker `agy` melalui Orca.
- **Batas verifikasi:** aplikasi tidak dijalankan dan fitur tidak diuji melalui klik. Dokumen ini menjelaskan implementasi yang terlihat pada kode, bukan jaminan keberhasilan pada semua dokumen atau kondisi komputer.

## Daftar isi

1. [Aplikasi apakah ini?](#1-aplikasi-apakah-ini)
2. [Kegunaan utama](#2-kegunaan-utama)
3. [All Tools atau Beranda](#3-menu-all-tools-atau-beranda)
4. [Merge PDF](#4-menu-merge-pdf)
5. [Split PDF](#5-menu-split-pdf)
6. [Compress PDF](#6-menu-compress-pdf)
7. [Organize Pages](#7-menu-organize-pages)
8. [Image to PDF](#8-menu-image-to-pdf)
9. [PDF to Image](#9-menu-pdf-to-image)
10. [Batch Rename](#10-menu-batch-rename)
11. [Fitur pendukung](#11-fitur-pendukung-aplikasi)
12. [Batasan dan perbedaan backend dengan antarmuka](#12-batasan-dan-perbedaan-backend-dengan-antarmuka)
13. [Fitur yang belum tersedia sebagai menu utama](#13-fitur-yang-belum-tersedia-sebagai-menu-utama)
14. [Panduan memilih menu](#14-panduan-memilih-menu)
15. [Contoh alur kerja](#15-contoh-alur-kerja)
16. [Ringkasan verifikasi agy](#16-ringkasan-verifikasi-agy)

## 1. Aplikasi apakah ini?

**LocalPDF Studio adalah aplikasi pengolah PDF, gambar, dan penamaan file massal yang menjalankan pemrosesan pada komputer yang menjalankan aplikasi.**

Aplikasi ini cocok untuk pekerjaan administrasi, pengolahan hasil scan, penyusunan dokumen, dan pengarsipan digital. Posisinya adalah toolkit pengolahan berkas dan halaman PDF, bukan editor isi PDF lengkap.

### 1.1 Cara aplikasi digunakan

Aplikasi dapat digunakan melalui:

- **Jendela desktop:** launcher membuka antarmuka web lokal sebagai jendela aplikasi.
- **Browser:** pengguna mengakses server lokal, secara default pada `http://127.0.0.1:8000`.

Launcher desktop mencoba membuka antarmuka dengan urutan:

1. Microsoft Edge App Mode.
2. PyWebView jika tersedia.
3. Browser default sebagai fallback.

Launcher mengutamakan port 8000 dan dapat memilih port lain jika port tersebut sedang digunakan.

### 1.2 Arti pemrosesan lokal

Pada penggunaan lokal standar, dokumen diproses oleh aplikasi di komputer pengguna, bukan melalui layanan konversi PDF cloud pihak ketiga.

Istilah **upload** pada antarmuka berarti browser mengirimkan berkas ke server aplikasi. Jika server aplikasi berjalan di komputer sendiri, pengiriman itu tetap menuju server lokal komputer tersebut.

Jika aplikasi dikonfigurasi untuk berjalan pada komputer lain, lokasi pemrosesan dan folder yang diakses mengikuti komputer yang menjalankan server. Karena itu, klaim lokal perlu dipahami berdasarkan cara aplikasi dijalankan, bukan sekadar perangkat yang membuka browser.

Pemrosesan lokal tidak dengan sendirinya menjadi jaminan keamanan menyeluruh, kepatuhan standar tertentu, atau penghapusan semua file sementara.

### 1.3 Teknologi utama

| Bagian | Teknologi |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Pengolahan PDF | PyMuPDF/fitz dan pypdf |
| Pengolahan gambar | Pillow/PIL |
| Antarmuka | Jinja2, Tailwind CSS, JavaScript |
| Pengurutan drag-and-drop | SortableJS |
| Ikon | Lucide |
| Launcher desktop | Edge App Mode, PyWebView, atau browser fallback |

**Rujukan kode:** `app.py:59`, `desktop_app.py:36`, `desktop_app.py:158`.

## 2. Kegunaan utama

LocalPDF Studio membantu pengguna untuk:

1. Menggabungkan beberapa PDF menjadi satu dokumen.
2. Memisahkan PDF berdasarkan halaman atau rentang tertentu.
3. Mengambil sebagian halaman menjadi PDF baru.
4. Memperkecil ukuran PDF dengan beberapa pilihan tingkat kompresi.
5. Menyusun ulang, mengulang, memutar, atau menghapus halaman PDF.
6. Menambahkan halaman dari PDF lain ke susunan dokumen.
7. Mengubah gambar menjadi PDF gabungan atau beberapa PDF berdasarkan kelompok.
8. Mengubah halaman PDF menjadi gambar JPG atau PNG.
9. Mengganti nama banyak file, termasuk memperbaiki nomor hasil scan.

### Contoh pekerjaan

- Menggabungkan formulir, identitas, dan surat pendukung menjadi satu lampiran.
- Memisahkan berkas scan berdasarkan jenis dokumen.
- Memperbaiki urutan halaman hasil scan yang terbalik.
- Mengubah kumpulan gambar scan menjadi PDF per dokumen.
- Menomori ulang arsip agar konsisten.
- Menyiapkan PDF dengan ukuran lebih kecil untuk dikirim.

## 3. Menu All Tools atau Beranda

### 3.1 Fungsi

Beranda menampilkan seluruh alat yang tersedia sebagai pintu masuk aplikasi.

Terdapat tujuh pilihan:

1. Merge PDF.
2. Split PDF.
3. Compress PDF.
4. Organize Pages.
5. Image to PDF.
6. PDF to Image.
7. Batch Rename.

Setiap pilihan memiliki deskripsi singkat dan tautan menuju halaman alat terkait.

### 3.2 Navigasi

Toolbar utama menyediakan akses cepat ke:

- **All Tools:** kembali ke daftar seluruh alat.
- **Merge:** membuka penggabungan PDF.
- **Split:** membuka pemisahan PDF.
- **Compress:** membuka kompresi PDF.

Menu Organize Pages, Image to PDF, PDF to Image, dan Batch Rename dapat diakses melalui kartu pada beranda.

Toolbar juga menyediakan tombol pergantian tema terang dan gelap. Pada layar kecil tersedia menu navigasi yang dapat dibuka melalui kontrol pemilihan alat.

**Rujukan kode:** `templates/index.html:11`, `templates/base.html:32`.

## 4. Menu Merge PDF

**Alamat menu:** `/tool/merge`.

### 4.1 Fungsi utama

Menggabungkan satu atau beberapa file PDF menjadi satu dokumen PDF baru.

Menu ini beroperasi terutama pada tingkat **file**: pengguna menentukan file yang dimasukkan dan urutan file tersebut.

### 4.2 Input

- Memilih beberapa PDF melalui pemilih file.
- Menarik dan meletakkan PDF ke area unggah.
- Menambahkan PDF lagi setelah daftar awal terbentuk.

### 4.3 Pengaturan urutan

Tersedia beberapa cara:

- **Drag-and-drop:** menggeser kartu file ke posisi yang diinginkan.
- **Naik dan Turun:** memindahkan file satu posisi.
- **Urutan alami A-Z:** memahami angka pada nama, misalnya `1.pdf`, `2.pdf`, lalu `10.pdf`.
- **Urutan alami Z-A:** kebalikan dari urutan alami.
- **Balik urutan:** membalik susunan yang sedang tampil.

Urutan daftar menentukan urutan isi dokumen hasil.

### 4.4 Rotasi

Setiap kartu file memiliki tombol putar 90°. Menekan beberapa kali menghasilkan rotasi 90°, 180°, 270°, kemudian kembali ke posisi awal.

**Penting:** rotasi pada menu Merge diterapkan ke seluruh halaman dalam file terkait. Antarmuka ini bukan pengaturan rotasi halaman individual. Untuk memutar halaman tertentu, gunakan Organize Pages.

### 4.5 Mengeluarkan file dari daftar

Pengguna dapat:

- Mengeluarkan satu file dari daftar penggabungan.
- Membersihkan seluruh daftar.

Tindakan ini mengubah susunan kerja dan bukan perintah menghapus dokumen asli pada disk.

### 4.6 Informasi yang ditampilkan

- Nama file.
- Jumlah halaman per file.
- Ukuran file.
- Thumbnail halaman awal jika tersedia.
- Jumlah total file.
- Jumlah total halaman.

### 4.7 Output dan penyimpanan

- Hasil berupa satu PDF.
- Nama file hasil dapat ditentukan.
- Nama awal yang disediakan adalah `merged_document.pdf`.
- Folder penyimpanan dapat dipilih.
- Hasil dapat diunduh melalui browser.
- Folder hasil dapat dibuka melalui File Explorer setelah penyimpanan berhasil.

### 4.8 Contoh penggunaan

Input:

```text
01_Formulir.pdf
02_Identitas.pdf
03_Lampiran.pdf
```

Output yang dapat ditentukan:

```text
Berkas_Pendaftaran.pdf
```

Isi hasil mengikuti urutan file pada daftar.

### 4.9 Batasan

Backend mendukung daftar halaman tertentu untuk setiap file, tetapi kontrol pemilihan halaman belum tersedia pada UI Merge saat ini. Antarmuka mengirimkan seluruh halaman dari setiap PDF yang dipilih.

**Rujukan kode:** `templates/merge.html:155`, `templates/merge.html:302`, `templates/merge.html:346`, `core/merger.py:6`.

## 5. Menu Split PDF

**Alamat menu:** `/tool/split`.

### 5.1 Fungsi utama

Memisahkan satu PDF menjadi beberapa PDF, atau mengambil halaman tertentu menjadi satu PDF baru.

Input berupa satu PDF melalui pemilih file atau drag-and-drop.

### 5.2 Mode Berdasarkan Rentang

Setiap bagian yang dipisahkan koma menjadi kelompok output tersendiri.

Contoh:

```text
1-3, 4-6, 7-10
```

Hasil:

- PDF pertama berisi halaman 1 sampai 3.
- PDF kedua berisi halaman 4 sampai 6.
- PDF ketiga berisi halaman 7 sampai 10.

Seluruh hasil dikemas dalam ZIP.

**Cocok untuk:** memisahkan dokumen scan gabungan berdasarkan bagian atau dokumen asal.

### 5.3 Mode Ekstrak Semua Jadi PDF Tunggal

Setiap halaman dibuat menjadi satu PDF tersendiri.

Contoh: PDF berisi lima halaman menghasilkan lima PDF, masing-masing berisi satu halaman. Seluruh hasil dikemas dalam ZIP.

**Cocok untuk:** mengarsipkan setiap lembar secara terpisah.

### 5.4 Mode Ekstrak Halaman Pilihan ke 1 PDF

Mengambil halaman yang ditentukan lalu menyimpannya ke satu PDF baru.

Contoh:

```text
1-3, 7, 10
```

Hasil berisi halaman 1, 2, 3, 7, dan 10.

**Cocok untuk:** mengambil bagian penting dari dokumen panjang.

### 5.5 Default dan informasi

- Mode awal: Berdasarkan Rentang.
- Isian rentang awal: `1-2, 3-4`.
- Kotak rentang disembunyikan pada mode satu PDF per halaman.
- Nama file, ukuran, dan total halaman ditampilkan.
- Kartu nomor halaman disediakan sebagai panduan.

### 5.6 Output dan penyimpanan

| Mode | Output |
|---|---|
| Berdasarkan rentang | ZIP berisi beberapa PDF |
| Satu PDF per halaman | ZIP berisi PDF untuk setiap halaman |
| Ekstrak pilihan | Satu PDF |

Pengguna dapat mengunduh hasil, memilih folder penyimpanan, membuka folder hasil, dan mengganti dokumen untuk pemrosesan berikutnya.

Jika hasil berupa ZIP dan folder tujuan diisi, mekanisme penyimpanan menyalin ZIP sekaligus mengekstrak isinya ke folder tujuan.

### 5.7 Batasan

- Pemilihan halaman dilakukan melalui isian nomor/rentang, bukan checkbox thumbnail.
- Kartu halaman hanya menampilkan nomor, bukan isi halaman sebenarnya.
- Pada ekstraksi pilihan melalui isian rentang, halaman diurutkan dan duplikasi dibuang.
- Untuk urutan seperti `3,1,2,2`, gunakan Organize Pages.

**Rujukan kode:** `templates/split.html:70`, `templates/split.html:197`, `core/splitter.py:7`, `core/splitter.py:37`, `app.py:676`.

## 6. Menu Compress PDF

**Alamat menu:** `/tool/compress`.

### 6.1 Fungsi utama

Mengurangi ukuran PDF melalui optimasi struktur dan, pada tingkat tertentu, kompresi ulang gambar.

Menu memproses satu PDF dalam satu proses.

### 6.2 Tingkat kompresi

| Tingkat | Cara kerja | Penggunaan |
|---|---|---|
| Ringan | Optimasi struktur tanpa kompresi ulang gambar | Mempertahankan gambar sumber |
| Optimal | Optimasi struktur dan kompresi ulang gambar seimbang | Kebutuhan sehari-hari |
| Maksimal | Optimasi lebih agresif dan penurunan kualitas/resolusi gambar | Mengutamakan ukuran hasil lebih kecil |

#### Kompresi Ringan

Fokus pada:

- Pembersihan objek internal yang tidak diperlukan.
- Kompresi struktur dan stream PDF.
- Optimasi penyimpanan internal.

Tidak menjalankan tahap kompresi ulang gambar.

#### Kompresi Optimal

Merupakan pilihan default.

Konfigurasi engine:

- Parameter kualitas gambar: 85.
- Ambang resolusi gambar: 300 DPI.
- Target resolusi untuk gambar yang memenuhi ambang: 150 DPI.
- Disertai optimasi struktur.

#### Kompresi Maksimal

Konfigurasi lebih agresif:

- Parameter kualitas gambar: 50.
- Ambang resolusi gambar: 200 DPI.
- Target resolusi untuk gambar yang memenuhi ambang: 96 DPI.
- Usaha kompresi struktur lebih tinggi.

Parameter kualitas tersebut bukan persentase jaminan kualitas visual.

### 6.3 Informasi hasil

Antarmuka menampilkan:

- Ukuran awal.
- Ukuran hasil.
- Persentase penghematan ukuran yang dihitung aplikasi.

### 6.4 Output dan penyimpanan

- Output berupa PDF.
- Nama dibentuk otomatis dengan pola `[nama_asal]_compressed.pdf`.
- Contoh: `laporan.pdf` menjadi `laporan_compressed.pdf`.
- Dapat diunduh melalui browser.
- Dapat disimpan ke folder pilihan.
- Folder hasil dapat dibuka melalui File Explorer.

### 6.5 Batasan

- Tidak ada jaminan setiap PDF menjadi lebih kecil.
- Dokumen yang sudah optimal dapat hanya berkurang sedikit atau menghasilkan file lebih besar.
- Mode Optimal dan Maksimal dapat menurunkan kualitas gambar, termasuk teks yang merupakan bagian dari gambar scan.
- Jika kompresi ulang gambar gagal, kode mencoba melanjutkan dengan optimasi penyimpanan.
- Modul kompresor memiliki fallback pypdf jika fitz tidak tersedia; pada jalur ini perbedaan strategi tiga level tidak diterapkan penuh.

**Rujukan kode:** `templates/compress.html:66`, `templates/compress.html:212`, `core/compressor.py:15`, `app.py:744`.

## 7. Menu Organize Pages

**Alamat menu:** `/tool/organize`.

### 7.1 Fungsi utama

Menyusun isi PDF pada tingkat halaman secara visual.

Menu ini digunakan untuk memperbaiki susunan dokumen, bukan mengedit teks atau gambar di dalam halaman.

### 7.2 Input

- Memuat satu PDF sebagai dokumen awal.
- Menambahkan satu atau beberapa PDF lain ke susunan yang sedang dikerjakan.

Halaman PDF tambahan masuk ke daftar dan dapat dipindahkan ke posisi yang diinginkan.

### 7.3 Pratinjau isi halaman

Setiap halaman mempunyai thumbnail isi sebenarnya.

Pratinjau besar menyediakan:

- Zoom masuk dan keluar.
- Halaman sebelumnya dan berikutnya.
- Navigasi panah keyboard.
- Nama dokumen sumber.
- Nomor halaman asli.
- Posisi halaman dalam susunan.
- Informasi jika halaman ditandai hapus.

### 7.4 Mengatur urutan

Pilihan yang tersedia:

- Drag-and-drop.
- Tombol Naik dan Turun.
- Membalik seluruh urutan.
- Isian urutan halaman khusus.

### 7.5 Urutan halaman khusus

Contoh:

```text
3,1,2,2,5-7
```

Artinya:

1. Mengambil kartu posisi 3.
2. Lalu posisi 1.
3. Lalu posisi 2.
4. Mengulang posisi 2.
5. Lalu posisi 5 sampai 7.

Fitur ini mendukung:

- Perubahan urutan.
- Pengambilan sebagian halaman.
- Pengulangan halaman.
- Rentang maju atau mundur.

**Nomor mengacu pada posisi kartu saat ini**, bukan selalu nomor halaman asli dokumen.

Halaman yang tidak dicantumkan tidak masuk ke susunan baru setelah urutan diterapkan. Posisi yang sedang ditandai hapus tidak dapat digunakan sampai dikembalikan.

Isian urutan khusus dibatasi sampai **2.000 entri halaman**. Batas ini berlaku pada hasil parsing isian urutan khusus, bukan klaim batas keseluruhan seluruh fungsi PDF aplikasi.

### 7.6 Rotasi

- Memutar halaman tertentu per 90°.
- Memutar seluruh halaman sekaligus.

### 7.7 Menghapus dan mengembalikan halaman

Halaman dapat ditandai untuk tidak disertakan dalam output.

Sebelum menyimpan, tanda hapus dapat dibatalkan. Tindakan ini tidak menghapus file PDF sumber.

### 7.8 Output dan penyimpanan

- Hasil berupa satu PDF baru.
- Nama hasil dapat ditentukan.
- Nama awal: `organized_document.pdf`.
- Folder tujuan dapat dipilih.
- Hasil dapat diunduh.
- Folder hasil dapat dibuka melalui File Explorer.
- Setidaknya satu halaman harus tetap aktif.

### 7.9 Contoh penggunaan

Hasil scan memiliki urutan terbalik dan satu halaman salah orientasi. Pengguna dapat:

1. Membalik urutan halaman.
2. Memutar halaman yang salah.
3. Menambahkan sampul dari PDF lain.
4. Mengeluarkan halaman kosong.
5. Menyimpan hasil sebagai PDF baru.

**Rujukan kode:** `templates/organize.html:254`, `templates/organize.html:287`, `templates/organize.html:310`, `templates/organize.html:460`, `core/splitter.py:134`.

## 8. Menu Image to PDF

**Alamat menu:** `/tool/image-to-pdf`.

### 8.1 Fungsi utama

Mengubah kumpulan gambar menjadi satu atau beberapa PDF dengan pengaturan urutan, pengelompokan, tampilan halaman, dan penamaan hasil.

Menu ini menyediakan pengaturan yang cukup rinci untuk pekerjaan hasil scan.

### 8.2 Sumber gambar

#### Mode Folder Lokal

- Memilih folder melalui dialog folder.
- Atau memasukkan lokasi folder lalu memindainya dari halaman aplikasi lokal.
- Memuat gambar yang didukung langsung dari folder tersebut.
- Merupakan mode sumber awal.

Format yang dikenali:

```text
.jpg
.jpeg
.png
.webp
.bmp
.tif
.tiff
```

**Pemindaian tidak rekursif:** hanya file langsung di folder pilihan yang dibaca. Subfolder tidak ditelusuri otomatis.

#### Mode Upload

- Memilih banyak gambar.
- Menarik dan meletakkan gambar ke area unggah.
- Menambahkan gambar lagi ke daftar.

### 8.3 Seleksi gambar

Setiap gambar memiliki checkbox:

- Dicentang: ikut diproses.
- Tidak dicentang: diabaikan.

Tersedia juga:

- Pilih semua.
- Batalkan pilihan semua.
- Jumlah gambar total.
- Jumlah gambar terpilih.

Membatalkan centang tidak menghapus file.

### 8.4 Urutan gambar

- Drag-and-drop.
- Tombol Naik dan Turun.
- Urutan alami A-Z.
- Urutan alami Z-A.
- Balik urutan.

Urutan menentukan posisi halaman PDF dan dasar pembagian kelompok.

### 8.5 Rotasi dan pemeriksaan gambar

Pengguna dapat:

- Memutar satu gambar per 90°.
- Memutar semua gambar.
- Membuka tampilan besar atau lightbox.
- Membuka lightbox dari thumbnail, tombol zoom, atau klik kanan kartu.
- Zoom masuk dan keluar.
- Mengembalikan zoom ke 100%.
- Berpindah gambar dengan tombol atau panah keyboard.
- Menutup tampilan besar dengan Escape.

Pada mode terpisah, kartu dan lightbox dapat menampilkan informasi seperti:

```text
File #2 (1/3)
```

Artinya gambar tersebut akan menjadi halaman pertama dari tiga halaman pada PDF kelompok kedua.

Pada mode upload, lightbox saat ini memakai thumbnail hasil unggah, sehingga bukan selalu gambar asli beresolusi penuh.

### 8.6 Mode Gabungkan Menjadi Satu PDF

Semua gambar yang dicentang dibuat menjadi satu PDF.

- Satu gambar menjadi satu halaman.
- Urutan mengikuti daftar.
- Nama hasil dapat ditentukan.
- Nama awal: `Scan_Gabungan.pdf`.

Contoh: 20 gambar scan menghasilkan satu PDF berisi 20 halaman.

### 8.7 Mode PDF Terpisah

Terdapat tiga pilihan pengelompokan.

#### Auto Grouping per N Gambar

Membentuk satu PDF untuk setiap sejumlah gambar.

Contoh:

- Input 10 gambar.
- Ukuran kelompok 2 gambar.
- Hasil 5 PDF, masing-masing berisi 2 halaman.

Kontrol antarmuka menyediakan rentang isian 1 sampai 100 dengan nilai awal 2. Ini merupakan atribut kontrol UI, bukan jaminan batas validasi backend yang sama.

#### Satu Gambar = Satu PDF

Setiap gambar menghasilkan satu PDF tersendiri.

Contoh: 10 gambar menghasilkan 10 PDF.

#### Rentang Gambar Tertentu

Menentukan kelompok khusus dengan isian seperti:

```text
1-4, 5-8
```

Gambar di luar rentang khusus tetap diproses menggunakan ukuran **Default Grouping**.

Contoh:

- Input 10 gambar.
- Rentang khusus `1-4, 5-8`.
- Default grouping 1.

Hasil:

- PDF pertama: gambar 1 sampai 4.
- PDF kedua: gambar 5 sampai 8.
- PDF ketiga: gambar 9.
- PDF keempat: gambar 10.

Nomor rentang mengacu pada urutan gambar yang terpilih. Nomor tersebut berubah jika pilihan atau urutan gambar berubah.

### 8.8 Penamaan PDF terpisah

#### Nama asli

- Satu gambar: memakai nama dasar gambar.
- Kelompok gambar: memakai nama gambar pertama dan terakhir sebagai dasar penamaan.
- Backend menambahkan pembeda jika nama output bentrok dalam hasil yang dibuat.

#### Nomor urut

Pengaturan:

- Penomoran naik atau turun.
- Nomor awal.
- Padding nol.
- Prefix.
- Suffix.

Contoh:

```text
Arsip_001_final.pdf
Arsip_002_final.pdf
Arsip_003_final.pdf
```

Menu Image to PDF memakai langkah naik/turun satu nomor pada UI. Pengaturan step bebas tersedia pada Batch Rename, bukan sebagai kontrol terpisah di menu ini.

### 8.9 Preview kelompok dan nama

Sebelum konversi, antarmuka menampilkan:

- Jumlah PDF yang akan dibuat.
- Nama hasil yang direncanakan.
- Jumlah halaman per PDF.
- Nomor halaman yang tergabung.

Preview mengikuti pilihan, urutan, grouping, dan aturan penamaan yang aktif.

### 8.10 Layout halaman

| Pengaturan | Pilihan pada UI | Default |
|---|---|---|
| Ukuran kertas | Fit/Asli, A4, Letter | Fit/Asli |
| Orientasi | Otomatis, Potret, Lanskap | Otomatis |
| Margin | Tanpa margin, kecil, besar | Tanpa margin |

Penjelasan:

- **Fit:** ukuran halaman mengikuti dimensi gambar.
- **A4/Letter:** gambar ditempatkan pada ukuran kertas tetap dengan proporsi dipertahankan.
- **Otomatis:** pada kertas tetap, orientasi mengikuti bentuk gambar.
- **Potret/Lanskap:** mengatur orientasi pada ukuran kertas tetap.
- **Margin kecil:** parameter internal 20 point.
- **Margin besar:** parameter internal 40 point.

Pada mode Fit, dimensi gambar tetap menjadi dasar ukuran halaman; pengaturan orientasi bukan perintah memutar gambar. Gunakan tombol rotasi jika ingin mengubah arah gambar.

Backend juga mengenal ukuran Legal, tetapi pilihan tersebut belum tersedia pada dropdown UI.

### 8.11 Penanganan gambar

Pemrosesan meliputi:

- Penanganan orientasi EXIF yang didukung.
- Latar putih untuk gambar transparan saat melalui tahap persiapan gambar.
- Pemeliharaan proporsi gambar pada halaman.
- Penulisan PDF dengan checkpoint bertahap pada implementasi writer saat ini.
- Konversi dijalankan melalui proses worker terpisah dari event loop server.

Mekanisme tersebut merupakan detail implementasi, bukan bukti angka performa atau jaminan kapasitas tertentu.

### 8.12 Output dan penyimpanan

| Mode | Unduhan browser | Jika folder tujuan diisi |
|---|---|---|
| Gabungan | Satu PDF | PDF disalin ke folder tujuan |
| Terpisah | ZIP berisi PDF | PDF diekstrak ke folder tujuan tanpa menyalin ZIP |

Jika penyimpanan folder gagal, aplikasi memberikan peringatan dan hasil tetap dapat diunduh.

### 8.13 Menghapus gambar

**Mode upload:** tombol hapus mengeluarkan gambar dari antrean, bukan menghapus file asli pada lokasi asal pengguna.

**Mode folder lokal:** tombol hapus memproses penghapusan file sumber setelah konfirmasi, baik satu gambar maupun gambar terpilih secara massal.

> **Peringatan:** pada Windows, kode mencoba memindahkan file ke Recycle Bin. Jika operasi itu gagal, terdapat fallback penghapusan langsung melalui `unlink`. Karena itu, penghapusan lokal tidak dijamin selalu dapat dipulihkan dari Recycle Bin. Jika hanya ingin mengecualikan gambar dari konversi, batalkan centangnya, jangan gunakan tombol hapus.

**Rujukan kode:** `templates/image_to_pdf.html:143`, `templates/image_to_pdf.html:491`, `templates/image_to_pdf.html:610`, `templates/image_to_pdf.html:813`, `templates/image_to_pdf.html:999`, `core/image_converter.py:153`, `core/image_pdf_writer.py:12`, `core/utils.py:141`.

## 9. Menu PDF to Image

**Alamat menu:** `/tool/pdf-to-image`.

### 9.1 Fungsi utama

Mengubah setiap halaman PDF menjadi file gambar.

Hasilnya adalah render halaman secara keseluruhan, bukan hanya mengambil foto atau ilustrasi yang tertanam dalam PDF.

### 9.2 Input

- Satu PDF melalui pemilih file.
- Atau drag-and-drop.

### 9.3 Format output

#### JPG

Cocok untuk:

- Dokumen scan.
- Berbagi gambar dengan kebutuhan ukuran relatif ringan.
- Kebutuhan tanpa transparansi.

#### PNG

Cocok untuk:

- Hasil raster tanpa kompresi lossy JPG.
- Teks, garis, dan elemen grafis.
- Kebutuhan transparansi yang didukung renderer.

JPG merupakan pilihan awal.

### 9.4 Resolusi

| DPI | Kegunaan |
|---|---|
| 100 | Lebih ringan dan cepat dibanding pilihan resolusi lebih tinggi |
| 150 | Pilihan default untuk kebutuhan umum |
| 300 | Resolusi lebih tinggi, dengan kebutuhan ukuran dan memori lebih besar |

### 9.5 Output dan penyimpanan

- Setiap halaman menjadi satu gambar.
- Gambar dikemas dalam ZIP.
- Pola nama ZIP: `[nama_asal]_images.zip`.
- Hasil dapat diunduh melalui browser.
- Folder penyimpanan dapat dipilih.
- Jika folder diisi, ZIP disalin sekaligus isinya diekstrak ke folder tersebut.
- Folder hasil dapat dibuka melalui File Explorer.

### 9.6 Batasan

- UI belum memiliki kontrol pemilihan halaman tertentu.
- Payload dari UI tidak mengirimkan parameter halaman, sehingga seluruh halaman diproses.
- Backend sudah memiliki parameter seleksi halaman, tetapi belum diekspos melalui menu.
- UI hanya menyediakan 100, 150, dan 300 DPI, bukan isian angka bebas.
- Kartu halaman hanya menampilkan nomor, bukan pratinjau isi PDF.
- Fitur ini bukan OCR dan bukan ekstraksi teks.

Jika hanya membutuhkan beberapa halaman melalui UI, pengguna dapat mengambilnya terlebih dahulu dengan Split PDF, lalu mengonversi PDF hasilnya.

**Rujukan kode:** `templates/pdf_to_image.html:75`, `templates/pdf_to_image.html:93`, `templates/pdf_to_image.html:192`, `templates/pdf_to_image.html:221`, `core/image_converter.py:260`, `app.py:435`.

## 10. Menu Batch Rename

**Alamat menu:** `/tool/rename`.

### 10.1 Fungsi utama

Mengganti nama banyak file sekaligus tanpa mengubah isi dokumennya.

Berguna untuk merapikan arsip dan memperbaiki penomoran hasil scan.

### 10.2 Mode Folder Lokal Komputer

Mengganti nama file langsung pada folder sumber.

Fitur:

- Memilih atau memindai folder.
- Melihat preview perubahan.
- Menjalankan rename setelah konfirmasi.
- Membatalkan rename terakhir melalui Undo.

Mode folder lokal merupakan mode awal.

**Batasan format:** eksekusi lokal secara default hanya memproses:

```text
.pdf
.jpg
.jpeg
.png
```

Pemindaian folder dapat menampilkan WEBP, BMP, TIF, dan TIFF, tetapi format tersebut dilewati oleh pemroses rename lokal saat ini.

### 10.3 Mode Upload File

- Mengunggah banyak file.
- Menerapkan aturan nama.
- Mengunduh ZIP berisi file dengan nama baru.

Mode ini tidak mengganti nama file asli pada lokasi asal pengguna.

### 10.4 Aturan Geser Nomor atau Shift

Menggeser angka pertama yang ditemukan pada nama dasar file.

Contoh offset `+3`:

```text
scan_005.pdf menjadi scan_008.pdf
```

Pengaturan:

- Offset positif atau negatif.
- Filter minimum nomor.
- Jumlah digit.
- Pemeliharaan panjang digit awal jika padding tidak ditentukan.

Default:

- Tipe aturan awal: Shift.
- Offset awal: `-1`.
- Padding awal: `0`, berarti otomatis mengikuti panjang angka yang ditemukan.

Jika hasil pergeseran negatif, angka dibatasi ke 0.

**Contoh penting:** pada `arsip_2026_005.pdf`, angka pertama adalah `2026`, sehingga angka itulah yang diproses, bukan otomatis `005`.

### 10.5 Aturan Nomor Urut Baru atau Sequence

Mengganti nama dasar dengan rangkaian nomor.

Pengaturan:

- Arah naik atau turun.
- Nomor awal.
- Step atau lompatan.
- Padding.
- Prefix.
- Suffix.

Default:

- Arah naik.
- Nomor awal 1.
- Step 1.
- Padding 3.

Contoh:

- Prefix `Dokumen_`.
- Mulai 1.
- Step 2.
- Padding 3.

Hasil:

```text
Dokumen_001.pdf
Dokumen_003.pdf
Dokumen_005.pdf
```

### 10.6 Aturan Cari dan Ganti atau Find & Replace

Mengganti teks pada nama dasar file.

Contoh:

```text
Scan_Lama_001.pdf menjadi Arsip_001.pdf
```

Pengaturan:

- Teks yang dicari.
- Teks pengganti.
- Opsi RegEx untuk pola yang lebih kompleks.

RegEx perlu digunakan dengan hati-hati agar pola dan hasil penggantian sesuai harapan. Kode memiliki pembatas panjang pola dan mekanisme pengujian substitusi dengan timeout, tetapi keberadaan mekanisme tersebut bukan jaminan keamanan menyeluruh.

### 10.7 Aturan Tambah Awalan/Akhiran

Mempertahankan nama dasar lalu menambahkan prefix dan suffix.

Contoh:

```text
001.pdf menjadi Surat_001_Selesai.pdf
```

Prefix dan suffix juga tersedia sebagai parameter umum untuk aturan lain sesuai logika pemrosesan.

### 10.8 Kapitalisasi

Pilihan:

- Tidak diubah.
- Semua huruf besar.
- Semua huruf kecil.
- Title Case.

Perubahan diterapkan pada nama dasar. Ekstensi dipertahankan.

### 10.9 Pengurutan daftar

- Urutan alami A-Z.
- Urutan alami Z-A.
- Balik urutan.

**Penting untuk mode lokal:** backend membaca ulang folder dan selalu mengurutkan file secara alami A-Z sebelum menjalankan rename. Payload eksekusi lokal tidak membawa urutan file dari UI. Karena itu, urutan penomoran aktual dapat berbeda dari preview Z-A atau Balik.

Pada mode upload, daftar file dikirim bersama permintaan eksekusi, berbeda dengan alur lokal tersebut.

### 10.10 Live Preview

Tabel menampilkan:

- Nomor urut.
- Nama asli.
- Nama baru.
- Status OK atau duplikat yang terdeteksi.
- Jumlah file.
- Jumlah nama yang berubah.

Preview perlu diperiksa sebelum rename, khususnya pada mode lokal. Peringatan duplikat bukan jaminan semua kemungkinan konflik nama telah dicegah.

### 10.11 Eksekusi lokal dan Undo

Rename lokal menggunakan dua tahap dengan nama sementara untuk mengurangi benturan saat perpindahan nama.

Riwayat disimpan pada folder yang sama dalam:

```text
rename_history.json
```

Undo membaca riwayat tersebut untuk mengembalikan nama sebelumnya.

Batasan:

- Hanya untuk rename terakhir.
- Tidak menyediakan riwayat pembatalan bertingkat.
- Riwayat ditimpa oleh proses rename berikutnya.
- Hanya tersedia pada mode lokal.
- Bergantung pada file dan lokasi yang masih sesuai dengan riwayat.
- Setelah Undo, file riwayat dihapus oleh implementasi.
- Bukan pengganti cadangan data dan tidak menjamin pemulihan pada semua konflik atau kegagalan.

**Rujukan kode:** `templates/rename.html:39`, `templates/rename.html:375`, `templates/rename.html:457`, `templates/rename.html:529`, `core/renamer.py:88`, `core/renamer.py:225`, `core/renamer.py:296`.

## 11. Fitur pendukung aplikasi

### 11.1 Tema terang dan gelap

Pengguna dapat mengganti tema melalui toolbar. Pilihan disimpan pada penyimpanan browser agar dapat digunakan kembali saat aplikasi dibuka.

### 11.2 Notifikasi

Aplikasi menampilkan pemberitahuan untuk:

- File berhasil dimuat.
- Proses selesai.
- Input tidak sesuai.
- Kesalahan pemrosesan.
- Perubahan urutan.
- Tindakan terhadap file atau folder.

### 11.3 Indikator pemrosesan

Tombol proses berubah menjadi status seperti:

- Memproses penggabungan.
- Mengekstrak halaman.
- Mengompres PDF.
- Menyusun PDF.
- Memproses gambar.

Indikator ini menunjukkan aplikasi sedang bekerja, bukan progress persentase yang terukur. Belum terlihat kontrol pembatalan pekerjaan konversi pada menu yang diperiksa.

### 11.4 Unduhan dan folder hasil

Sebagian besar alat PDF menyediakan:

- Tombol unduh hasil.
- Folder penyimpanan opsional.
- Informasi lokasi hasil jika penyimpanan berhasil.
- Tombol membuka folder hasil melalui File Explorer.
- Opsi menutup hasil atau memulai dokumen berikutnya.

Batch Rename berbeda: mode lokal mengubah nama langsung, sedangkan mode upload mengunduh ZIP.

### 11.5 Pengurutan tanpa drag-and-drop

Merge, Organize, dan Image to PDF menyediakan tombol Naik/Turun sebagai alternatif penggeseran kartu. Ini memungkinkan pengaturan urutan tanpa harus melakukan drag-and-drop.

### 11.6 Navigasi tambahan

- Tautan kembali ke beranda.
- Toolbar akses cepat.
- Tombol kembali ke bagian atas halaman.
- Dialog hasil dan notifikasi status.

### 11.7 File sementara

Aplikasi menggunakan direktori kerja untuk unggahan dan hasil.

Saat startup, kode menjalankan pembersihan file kerja lama dengan ambang usia dua jam. Ini bukan penghapusan otomatis langsung sesaat setelah setiap proses selesai, dan bukan jaminan penghapusan aman pada media penyimpanan.

### 11.8 Batas operasional

Kapasitas pemrosesan dipengaruhi:

- RAM.
- CPU.
- Ruang disk.
- Ukuran dan kompleksitas dokumen.
- Engine serta dependensi yang tersedia.

Terdapat rate limit API berdasarkan alamat klien dan endpoint, dengan konfigurasi utama:

| Jenis endpoint | Batas konfigurasi |
|---|---|
| Pemrosesan berat | 5 permintaan per menit |
| Upload | 10 permintaan per menit |
| Mutasi, termasuk rename/hapus | 10 permintaan per menit |
| Umum | 30 permintaan per menit |

Ini merupakan pembatas frekuensi permintaan, bukan jumlah halaman yang dapat diproses dalam satu dokumen. Endpoint pratinjau tertentu dikecualikan dari rate limit.

Karena itu, istilah "tanpa batas" pada materi aplikasi sebaiknya tidak ditafsirkan sebagai kapasitas tak terbatas atau tidak adanya pembatas teknis.

### 11.9 Mekanisme pembatasan akses

Kode memiliki mekanisme seperti:

- Registry direktori yang diizinkan pada operasi tertentu.
- Validasi path dan ekstensi pada endpoint tertentu.
- Pembatasan origin.
- Rate limiting.
- Validasi path saat ekstraksi ZIP.

Mekanisme tersebut adalah bagian implementasi, bukan hasil audit keamanan lengkap. Jangan menyimpulkan bahwa setiap endpoint memiliki perlindungan identik atau bahwa aplikasi memenuhi standar kepatuhan tertentu tanpa pemeriksaan tambahan.

**Rujukan kode:** `static/js/app.js:6`, `static/js/app.js:90`, `templates/macros.html:1`, `app.py:43`, `app.py:119`, `core/rate_limiter.py:17`.

## 12. Batasan dan perbedaan backend dengan antarmuka

| Bagian | Kemampuan atau perilaku backend | Kondisi UI dan dampaknya |
|---|---|---|
| Merge: rotasi | Rotasi per item diterapkan ke halaman-halaman dalam file | Tombol berada pada kartu file, bukan masing-masing halaman |
| Merge: seleksi halaman | Mendukung daftar halaman per file | Belum ada kontrol pemilih halaman pada UI |
| Split: pratinjau | Aplikasi memiliki endpoint render halaman untuk alat lain | UI Split hanya menampilkan nomor halaman |
| Compress: fallback | Modul memiliki jalur pypdf untuk kompresi stream | Strategi tiga level tidak diterapkan penuh pada jalur fallback |
| Organize: urutan khusus | Memproses operasi halaman | Parser urutan teks UI membatasi 2.000 entri |
| Image to PDF: Legal | Ukuran Legal ada pada konfigurasi backend | Dropdown hanya Fit, A4, dan Letter |
| Image to PDF: sumber folder | Membaca file langsung dengan iterasi direktori | Tidak memindai subfolder otomatis |
| Image to PDF: mode terpisah | Membuat ZIP untuk hasil kerja | Simpan folder mengekstrak PDF tanpa menyalin ZIP; unduhan tetap ZIP |
| Image to PDF: hapus lokal | Mencoba Recycle Bin, lalu fallback unlink | Pesan konfirmasi tidak boleh dianggap jaminan dapat dipulihkan |
| Image to PDF: lightbox upload | Item upload menggunakan thumbnail sebagai sumber tampilan | Zoom bukan jaminan pratinjau resolusi asli |
| PDF to Image: seleksi halaman | Mendukung parameter daftar halaman | UI tidak mengirimkan pilihan, sehingga seluruh halaman diproses |
| PDF to Image: DPI | Backend menerima angka DPI | UI hanya menyediakan 100, 150, dan 300 |
| Batch Rename: format lokal | Default hanya PDF, JPG, JPEG, dan PNG | Format gambar lain dapat muncul pada preview tetapi dilewati |
| Batch Rename: urutan lokal | Membaca ulang folder dan mengurutkan alami A-Z | Preview Z-A/Balik dapat berbeda dari penomoran aktual |
| Batch Rename: Undo | Menggunakan satu file riwayat terakhir | Tidak tersedia riwayat bertingkat atau Undo mode upload |

## 13. Fitur yang belum tersedia sebagai menu utama

Pada antarmuka dan rute yang diperiksa, belum terlihat menu khusus untuk:

- Mengedit teks di dalam PDF.
- OCR untuk menjadikan hasil scan sebagai teks yang dapat dicari.
- Konversi Word, Excel, atau PowerPoint.
- Tanda tangan digital.
- Anotasi atau highlight.
- Watermark.
- Redaksi permanen informasi sensitif.
- Enkripsi atau pengaturan password PDF.

Daftar ini menjelaskan menu yang terlihat pada aplikasi, bukan klaim bahwa seluruh library yang digunakan sama sekali tidak memiliki kemampuan tersebut.

## 14. Panduan memilih menu

| Kebutuhan | Menu |
|---|---|
| Menggabungkan beberapa PDF | Merge PDF |
| Memisahkan PDF per bagian | Split PDF |
| Membuat satu PDF untuk setiap halaman | Split PDF |
| Mengambil beberapa halaman menjadi satu PDF | Split PDF |
| Memperkecil ukuran file | Compress PDF |
| Mengatur ulang atau membalik urutan halaman | Organize Pages |
| Memutar halaman tertentu | Organize Pages |
| Mengulang halaman tertentu | Organize Pages melalui urutan khusus |
| Mengeluarkan halaman dari hasil | Organize Pages |
| Menambahkan halaman dari PDF lain | Organize Pages |
| Mengubah gambar menjadi satu PDF | Image to PDF |
| Membuat beberapa PDF berdasarkan kelompok gambar | Image to PDF |
| Memeriksa dan mengurutkan gambar scan sebelum konversi | Image to PDF |
| Mengubah halaman PDF menjadi JPG/PNG | PDF to Image |
| Mengganti nama banyak file | Batch Rename |
| Memperbaiki nomor dalam nama hasil scan | Batch Rename dengan Shift |
| Membuat nama file bernomor konsisten | Batch Rename dengan Sequence |

## 15. Contoh alur kerja

### 15.1 Hasil scan menjadi arsip PDF

1. Buka Image to PDF.
2. Muat folder gambar atau unggah gambar.
3. Periksa gambar melalui thumbnail/lightbox.
4. Batalkan centang gambar yang tidak ingin diproses.
5. Perbaiki rotasi dan urutan.
6. Pilih gabungan atau kelompok PDF.
7. Atur nama dan folder hasil.
8. Konversi.
9. Gunakan Organize Pages jika perlu menyisipkan atau menyusun ulang halaman.
10. Gunakan Compress PDF jika ukuran hasil perlu dikurangi.

### 15.2 Dokumen gabungan menjadi bagian terpisah

1. Buka Split PDF.
2. Muat PDF.
3. Pilih rentang, misalnya `1-3, 4-6, 7-10`.
4. Unduh ZIP atau simpan ke folder.
5. Jika perlu penamaan massal, gunakan Batch Rename dengan memperhatikan batasan mode lokal.

### 15.3 Mengambil halaman PDF menjadi gambar

1. Jika hanya membutuhkan sebagian halaman, ekstrak dulu dengan Split PDF.
2. Buka PDF to Image.
3. Muat PDF hasil ekstraksi.
4. Pilih JPG atau PNG.
5. Pilih 100, 150, atau 300 DPI.
6. Proses dan unduh ZIP atau simpan ke folder.

### 15.4 Merapikan nama hasil scan

1. Buat cadangan jika menggunakan mode rename lokal.
2. Buka Batch Rename.
3. Pilih folder atau upload file.
4. Pilih Shift, Sequence, Replace, atau Prefix/Suffix.
5. Periksa nama baru dan peringatan duplikat.
6. Untuk mode lokal, ingat bahwa backend menggunakan urutan alami A-Z dan hanya memproses format default yang didukung.
7. Jalankan rename.
8. Jika diperlukan, gunakan Undo sebelum melakukan rename berikutnya dan sebelum memindahkan file.

## 16. Ringkasan verifikasi agy

Worker `agy` melalui Orca telah memeriksa kode aplikasi dan melaporkan penyelesaian tugas pemeriksaan fitur secara read-only.

Hasil pemeriksaan menguatkan:

- Identitas LocalPDF Studio sebagai aplikasi web/desktop lokal.
- Keberadaan tujuh alat utama.
- Opsi nyata pada antarmuka setiap menu.
- Perbedaan antara dukungan backend dan kontrol UI.
- Perbedaan penyimpanan ZIP dan ekstraksi folder.
- Batasan format dan urutan eksekusi Batch Rename lokal.
- Undo satu tingkat berdasarkan riwayat terakhir.
- Fallback penghapusan langsung pada penghapusan gambar lokal.
- Rate limit dan batas parser urutan khusus Organize.

### 16.1 Batas kesimpulan

- Pemeriksaan dilakukan terhadap kode, bukan uji operasional melalui browser.
- Tidak ada pengujian konversi dokumen dalam pekerjaan dokumentasi ini.
- Tidak ada perubahan kode aplikasi yang menjadi bagian dari verifikasi tersebut.
- Keberadaan kontrol atau logika pada kode tidak berarti seluruh kasus telah lulus pengujian.
- Tidak ada pengukuran performa, angka penghematan yang dijamin, atau sertifikasi keamanan yang dinyatakan oleh dokumen ini.

### 16.2 Kesimpulan

LocalPDF Studio paling sesuai untuk alur kerja:

**hasil scan → pemeriksaan gambar → pengelompokan PDF → penyusunan halaman → kompresi → pengarsipan dengan nama yang rapi.**

Pemrosesan dilakukan pada komputer yang menjalankan aplikasi. Penggunaan perlu tetap memperhatikan batasan antarmuka, kondisi dokumen, sumber daya komputer, serta tindakan yang mengubah nama atau menghapus file lokal.

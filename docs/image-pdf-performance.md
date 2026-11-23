# Konversi gambar dalam jumlah besar

Mesin konversi menggunakan penulis PDF yang sama untuk mode gabungan, per foto,
kelompok N foto, dan rentang custom. Pengelompokan menentukan file hasil; setiap
file ditulis secara bertahap, termasuk kelompok custom yang sangat besar.

## Penggunaan memori dan kualitas

- JPEG RGB/grayscale dengan orientasi EXIF 1, 3, 6, atau 8 serta rotasi kelipatan
  90 derajat dimasukkan langsung. Stream JPEG hasil identik dengan sumber.
- Format lain, EXIF dengan pencerminan, dan rotasi bebas diproses satu gambar
  pada satu waktu. Gambar perantara disimpan sebagai PNG lossless; transparansi
  diratakan ke putih. Tidak ada downsampling otomatis.
- Dokumen disimpan, ditutup, dan dibuka kembali setelah maksimum 64 halaman
  atau sebelum perkiraan data gambar batch berikutnya melewati 256 MiB. JPEG
  dihitung dari ukuran file; jalur Pillow dari perkiraan piksel hasil.
- Angka 256 MiB adalah anggaran batch, bukan batas keras memori proses. Satu
  gambar yang sangat besar, piksel hasil transformasi, cache pustaka, dan
  metadata PDF membutuhkan memori tambahan.
- Penyimpanan pertama membuat PDF baru; penyimpanan berikutnya incremental.
  File sementara yang rusak atau tidak dapat disimpan incremental menghasilkan
  error. Tidak ada fallback yang memuat seluruh dokumen ke memori.
- A4/Letter/Legal menggunakan ukuran halaman PDF dalam points, dengan resolusi
  gambar sumber dipertahankan. Mode fit memakai 100 DPI; margin dalam points.
  Ini memperbaiki ukuran fisik kertas yang sebelumnya dibuat sebagai kanvas
  piksel lalu disimpan pada 100 DPI.

## API dan penyimpanan

`POST /api/image-to-pdf` menerima opsi dan mengembalikan field hasil seperti
sebelumnya. Satu worker proses dengan metode Windows spawn menjalankan konversi;
permintaan berikutnya mengantre dan server dapat melayani permintaan lain.
Worker ditutup ketika lifespan server berakhir. Jalankan server melalui lifespan
FastAPI normal; pada pengujian gunakan context manager `TestClient`.

PDF kelompok ditulis ke disk sebelum ditambahkan ke ZIP. PDF/ZIP akhir baru
dipublikasikan dengan replace setelah pemeriksaan jumlah halaman/file selesai.
Kegagalan membersihkan direktori sementara pekerjaan dan mempertahankan hasil
lama jika publikasi belum terjadi. File sumber tidak diubah. Path gambar yang
hilang sekarang menggagalkan pekerjaan, sehingga halaman tidak dilewati diam-diam.

Hasil PDF terpisah tetap diekstrak ke folder pilihan pengguna; ZIP unduhan tetap
tersedia. Jika penyalinan/ekstraksi gagal, `success` menyatakan konversi selesai,
`saved_to_folder` bernilai null, dan field `warning` ditampilkan dalam hasil.
Penyalinan ke folder tujuan tidak merupakan transaksi multi-file; kegagalan
ekstraksi dapat meninggalkan sebagian file di folder tersebut.

Untuk kelompok besar, sediakan ruang disk untuk arsip dan PDF kelompok sementara
secara bersamaan. Mempertahankan JPEG asli dapat menghasilkan PDF lebih besar
daripada encoder lama yang melakukan kompresi lossy ulang.

## Verifikasi yang dapat diulang

```powershell
python -m pytest tests -q --basetemp tmp/pytest-image-pdf
node tests/test_organize_frontend.cjs
python scripts/benchmark_image_pdf.py 'PATH_TO_SCANS' --counts 100 500 1000
```

Benchmark memilih `IMG-*.jpeg` dengan urutan alami dan mengulang sumber bila
jumlah foto kurang. Laporan mencatat jumlah sumber unik dan pengulangan.
Setiap kasus berjalan dalam proses baru; pemantau eksternal membaca working set
dan private bytes Windows setiap 100 ms. Proses dihentikan di atas 2 GiB private
bytes; pengujian berikutnya tidak dijalankan bila konversi mencapai 1 GiB.
Puncak yang dilaporkan adalah puncak sampel, bukan jaminan batas untuk semua input.

Verifikasi memeriksa jumlah PDF/halaman dan hash stream JPEG pada setiap halaman
terhadap sumber sesuai urutan, serta merender halaman awal/tengah/akhir. Artefak
PDF uji dibersihkan; laporan JSON dan status tetap disimpan. Waktu konversi
dipisahkan dari waktu verifikasi. Benchmark ini tidak mencakup upload browser
atau penyalinan tambahan ke folder tujuan.

Tes regresi mencakup semua orientasi EXIF, rotasi bebas, ukuran kertas, margin,
transparansi, format BMP/WebP/TIFF, grayscale/CMYK, grouping, nama kembar, file
rusak/hilang, kegagalan penyimpanan dan publikasi, antrean worker, serta kesehatan
server saat konversi berlangsung. Suite regresi menghasilkan 111 tes lulus
(satu peringatan deprecation Pydantic pada kode yang sudah ada). Pemeriksaan
JavaScript frontend juga lulus. Build PyInstaller konfigurasi akhir selesai
pada 11 Oktober 2026; executable hasil build berhasil menjalankan worker
tersembunyi dengan konversi 20 halaman yang diverifikasi ulang.

## Hasil pengukuran

Uji awal menggunakan batch 16 halaman/64 MiB. Semua skenario 100 foto dan tiga
skenario 500 foto selesai; puncak private bytes konversi 65,1–138,7 MiB. Uji 500
foto gabungan memerlukan 327,43 detik dan berjalan bersamaan dengan build desktop.

Profiling menunjukkan penyimpanan incremental mendominasi waktu. Kode
[MuPDF pdf-write.c](https://github.com/ArtifexSoftware/mupdf/blob/master/source/pdf/pdf-write.c)
membandingkan isi file sebelumnya pada penyimpanan incremental. Default kemudian
disesuaikan menjadi 64 halaman/256 MiB untuk mengurangi frekuensi pembacaan ulang.
Percobaan 500 foto dengan konfigurasi ini selesai dalam 134,50 detik dengan
puncak private bytes 383,6 MiB. Aktivitas mesin berbeda sehingga angka ini bukan
perbandingan kecepatan dalam lingkungan terisolasi.

Data uji berasal dari 322 JPEG scan resolusi asli. Untuk 500 foto, 178 input
diulang; untuk 1.000 foto, 678 input diulang. Seluruh halaman diverifikasi dengan
hash JPEG, bukan hanya dihitung jumlahnya. Ketiga skenario 1.000 foto selesai
dengan konfigurasi akhir 64 halaman/256 MiB. Waktu berikut hanya tahap konversi,
di luar verifikasi.

| Mode, 1.000 foto | Hasil | Waktu konversi | Puncak private bytes | Ukuran hasil |
| --- | --- | --- | --- | --- |
| Gabungan | 1 PDF, 1.000 halaman | 341,06 detik | 387,5 MiB | 7,819 GB |
| Per foto | ZIP berisi 1.000 PDF | 395,64 detik | 69,2 MiB | 7,811 GB |
| Custom | ZIP berisi 3 PDF: 2, 996, dan 2 halaman | 609,17 detik | 384,3 MiB | 7,808 GB |

Ukuran GB menggunakan satuan desimal. Verifikasi tambahan masing-masing
memerlukan 28,40, 154,43, dan 79,02 detik. Seluruh stream JPEG sesuai sumber dan
urutan; halaman awal/tengah/akhir berhasil dirender. Mode kelompok N juga telah
diuji dengan kelompok dua foto pada 100 dan 500 foto serta tes regresi grouping.

Laporan terstruktur untuk seluruh 11 kasus ada di
[image-pdf-benchmark-results.json](image-pdf-benchmark-results.json). Angka memori
berlaku untuk dataset JPEG ini; gambar dengan format lain atau transformasi yang
memerlukan decode dapat menggunakan memori lebih besar. Hasil membuktikan bahwa
1.000 input pada dataset ini dapat selesai tanpa menumpuk semua piksel di RAM.

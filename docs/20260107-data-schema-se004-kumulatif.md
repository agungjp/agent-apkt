# APKT Agent - Data Schema SE004 Kumulatif

**Dokumen dibuat:** 7 Januari 2026  
**Versi:** 1.0

## Overview

Dokumen ini menjelaskan struktur data hasil parsing laporan SE004 Kumulatif dari sistem APKT.

## Output CSV Columns

| No  | Kolom                  | Tipe   | Deskripsi                 | Contoh                                 |
| --- | ---------------------- | ------ | ------------------------- | -------------------------------------- |
| 1   | `unit_induk`           | string | Nama unit PLN             | `DISTRIBUSI LAMPUNG`                   |
| 2   | `period_ym`            | string | Periode format YYYYMM     | `202511`                               |
| 3   | `period_label`         | string | Label periode             | `November 2025`                        |
| 4   | `jumlah_pelanggan`     | number | Jumlah pelanggan          | `2828036.0`                            |
| 5   | `saidi_total`          | number | SAIDI total (jam)         | `5.7905`                               |
| 6   | `saidi_total_menit`    | number | SAIDI total (menit)       | `347.4296`                             |
| 7   | `saifi_total`          | number | SAIFI total (kali)        | `3.7555`                               |
| 8   | `tanggal_cetak`        | string | Tanggal cetak laporan     | `07/01/2026`                           |
| 9   | `kode`                 | string | Kode gangguan             | `1`, `2`, ... `69`                     |
| 10  | `penyebab_gangguan`    | string | Deskripsi gangguan        | `Gangguan JTM`                         |
| 11  | `jml_plg_padam`        | number | Jumlah pelanggan padam    | `12345.0`                              |
| 12  | `jam_x_jml_plg_padam`  | number | Jam × Jumlah pelanggan    | `98765.0`                              |
| 13  | `saidi_jam`            | number | SAIDI per gangguan (jam)  | `0.1234`                               |
| 14  | `saifi_kali`           | number | SAIFI per gangguan (kali) | `0.0567`                               |
| 15  | `jumlah_gangguan_kali` | number | Jumlah gangguan (kali)    | `45.0`                                 |
| 16  | `lama_padam_jam`       | number | Lama padam (jam)          | `12.5`                                 |
| 17  | `kwh_tak_tersalurkan`  | number | kWh tidak tersalurkan     | `5678.0`                               |
| 18  | `row_type`             | string | Tipe baris                | `group` atau `detail`                  |
| 19  | `source_file`          | string | Nama file Excel sumber    | `se004_kumulatif_202511_WIL_ACEH.xlsx` |

## Row Types

### Group Rows (`row_type = "group"`)

Baris summary per kelompok:

- `KELOMPOK Distribusi`
- `KELOMPOK Transmisi`

Karakteristik:

- Kolom `kode` berisi nomor kelompok (1, 2)
- Kolom detail (`jml_plg_padam`, dll) kosong
- Digunakan untuk subtotal

### Detail Rows (`row_type = "detail"`)

Baris per kode gangguan:

- Kode 1-69 sesuai standar PLN

Karakteristik:

- Kolom `kode` berisi kode gangguan spesifik
- Kolom detail berisi nilai numerik
- Digunakan untuk analisis detail

## Kode Gangguan (Standar PLN)

| Kode | Penyebab Gangguan |
| ---- | ----------------- |
| 1    | Gangguan JTM      |
| 2    | Gangguan SR/APP   |
| 3    | Gangguan Trafo    |
| 4    | Gangguan JTR      |
| 5    | Gangguan Gardu    |
| 6    | Pemeliharaan JTM  |
| 7    | Pemeliharaan JTR  |
| ...  | ...               |
| 69   | Lainnya           |

## Data Source (Excel)

### Header Section

Lokasi di Excel (baris 1-10):

```
┌─────────────────────────────────────────────────┐
│ UNIT INDUK          : DISTRIBUSI LAMPUNG        │
│ PERIODE             : November 2025             │
│ JUMLAH PELANGGAN    : 2.828.036                 │
│ SAIDI               : 5,7905 Jam (347,4296 Menit)│
│ SAIFI               : 3,7555 Kali               │
│ TANGGAL CETAK       : 07/01/2026                │
└─────────────────────────────────────────────────┘
```

### Data Table

Lokasi di Excel (baris 11+):

```
┌─────┬───────────────────┬───────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│KODE │PENYEBAB GANGGUAN  │JML PLG    │JAM X    │SAIDI    │SAIFI    │JML      │LAMA     │
│     │                   │PADAM      │JML PLG  │(JAM)    │(KALI)   │GANGGUAN │PADAM    │
├─────┼───────────────────┼───────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│1    │KELOMPOK Distribusi│           │         │         │         │         │         │
│1    │Gangguan JTM       │12.345     │98.765   │0,1234   │0,0567   │45       │12,5     │
│2    │Gangguan SR/APP    │23.456     │87.654   │0,2345   │0,0678   │56       │23,6     │
│...  │...                │...        │...      │...      │...      │...      │...      │
│2    │KELOMPOK Transmisi │           │         │         │         │         │         │
│...  │...                │...        │...      │...      │...      │...      │...      │
└─────┴───────────────────┴───────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

## Validasi

### Required Fields

Setiap row harus memiliki:

- `unit_induk` - tidak boleh kosong
- `period_ym` - format YYYYMM valid
- `kode` - kode gangguan valid

### Numeric Ranges

| Kolom              | Min | Max  | Notes      |
| ------------------ | --- | ---- | ---------- |
| `saidi_total`      | 0   | 100+ | Dalam jam  |
| `saifi_total`      | 0   | 50+  | Dalam kali |
| `jumlah_pelanggan` | 0   | 10M+ | Integer    |

### Validation Warnings

Parser menghasilkan warning untuk:

- Nilai negatif
- Nilai di luar range normal
- Format tidak standar

## Sample Data

### CSV Format (semicolon delimiter)

```csv
unit_induk;period_ym;period_label;jumlah_pelanggan;saidi_total;saidi_total_menit;saifi_total;tanggal_cetak;kode;penyebab_gangguan;jml_plg_padam;jam_x_jml_plg_padam;saidi_jam;saifi_kali;jumlah_gangguan_kali;lama_padam_jam;kwh_tak_tersalurkan;row_type;source_file
DISTRIBUSI LAMPUNG;202511;November 2025;2.828.036,0;5,7905;347,4296;3,7555;07/01/2026;1;KELOMPOK Distribusi;;;;;;;;;group;se004_kumulatif_202511_DIST_LAMPUNG.xlsx
DISTRIBUSI LAMPUNG;202511;November 2025;2.828.036,0;5,7905;347,4296;3,7555;07/01/2026;1;Gangguan JTM;12.345;98.765;0,1234;0,0567;45;12,5;5678;detail;se004_kumulatif_202511_DIST_LAMPUNG.xlsx
```

### Google Sheets Format (number converted)

| unit_induk         | period_ym | jumlah_pelanggan | saidi_total |
| ------------------ | --------- | ---------------- | ----------- |
| DISTRIBUSI LAMPUNG | 202511    | 2828036          | 5.7905      |

## File Naming Convention

### Excel Files

```
se004_kumulatif_{period}_{unit_code}.xlsx
```

Contoh: `se004_kumulatif_202511_DIST_LAMPUNG.xlsx`

### CSV Files

```
se004_kumulatif_{period}_{hash}.csv
```

Contoh: `se004_kumulatif_202511_EYNP.csv`

- `hash` = 4 karakter random untuk uniqueness

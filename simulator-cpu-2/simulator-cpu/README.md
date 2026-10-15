# Simulator Penjadwalan CPU (K-2 Sistem Operasi, Kelas D)

Algoritma: FCFS, SJF non-preemptive, SRTF, Priority (non-preemptive dan preemptive), Round Robin.
Hanya memakai pustaka standar Python 3 (matplotlib hanya untuk `plot_gantt.py`).

## Menjalankan

```bash
python3 scheduler_sim.py                                   # dataset kelas P1-P5
python3 scheduler_sim.py --dataset dataset_kelas.csv --sensitivity
python3 scheduler_sim.py --dataset data_saya.csv --quantum 2 4 8
python3 -m unittest discover -s tests -v                   # uji
pip install matplotlib && python3 plot_gantt.py --out gambar
```

## Format dataset (CSV)

```
pid,arrival,burst,priority
P1,0,5,2
```

Angka priority kecil = prioritas tinggi. Input tidak valid menghasilkan pesan "Kesalahan input" (kode keluar 1).

## Aturan yang dipakai

- Tie-breaking: nilai kunci sama, lalu arrival lebih awal, lalu nomor proses lebih kecil.
- SRTF/Priority preemptive: proses berjalan tidak digantikan jika hanya seri (`tie_policy="keep"`).
- Round Robin: proses yang tiba tepat saat quantum habis masuk antrean sebelum proses yang di-preempt.
- Context switch = perpindahan antar dua irisan Gantt berurutan milik proses berbeda (IDLE tidak dihitung).
- Overhead context switch dianggap 0.

## Isi folder

- `scheduler_sim.py` algoritma, metrik, verifikasi, CLI
- `plot_gantt.py` gambar Gantt PNG
- `tests/test_scheduler.py` uji (nilai expected = hitungan manual)
- `hasil_program.txt` keluaran program yang dijalankan pada dataset kelas
- `gambar/` Gantt dan diagram

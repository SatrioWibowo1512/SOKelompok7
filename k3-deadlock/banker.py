#!/usr/bin/env python3
"""Simulasi pemeriksaan safe state (algoritma Banker) untuk K-3 Sistem Operasi Kelas D.

Pemakaian:
    python3 banker.py data/simulasi_aman.json
    python3 banker.py data/data_kelas.json

Kode keluar: 0 = safe state, 1 = unsafe state, 2 = data tidak valid.
Program ini hanya menghitung dari berkas masukan. Tidak ada data kelas yang tertanam di kode.
"""
import json
import sys


class DataError(ValueError):
    """Dilempar bila data masukan tidak valid."""


def muat(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validasi(d):
    """Pemeriksaan data sebelum perhitungan. Melempar DataError jika ada masalah."""
    for kunci in ("processes", "resources", "allocation", "max", "available"):
        if kunci not in d or d[kunci] is None:
            raise DataError(f"kunci '{kunci}' tidak ada atau masih kosong")
    n, m = len(d["processes"]), len(d["resources"])
    if n == 0 or m == 0:
        raise DataError("jumlah proses atau jenis sumber daya nol")
    for nama in ("allocation", "max"):
        mat = d[nama]
        if len(mat) != n:
            raise DataError(f"{nama}: jumlah baris {len(mat)} != jumlah proses {n}")
        for i, baris in enumerate(mat):
            if len(baris) != m:
                raise DataError(f"{nama}[{d['processes'][i]}]: panjang {len(baris)} != jenis sumber daya {m}")
    if len(d["available"]) != m:
        raise DataError(f"available: panjang {len(d['available'])} != jenis sumber daya {m}")
    semua = [x for b in d["allocation"] for x in b] + [x for b in d["max"] for x in b] + list(d["available"])
    for x in semua:
        if not isinstance(x, int) or isinstance(x, bool):
            raise DataError(f"nilai bukan bilangan bulat: {x!r}")
        if x < 0:
            raise DataError(f"nilai negatif: {x}")
    for i in range(n):
        for j in range(m):
            if d["allocation"][i][j] > d["max"][i][j]:
                raise DataError(
                    f"Allocation > Max pada {d['processes'][i]} / {d['resources'][j]} "
                    f"({d['allocation'][i][j]} > {d['max'][i][j]})")
    total = d.get("total")
    if total is not None:
        if len(total) != m:
            raise DataError("total: panjang tidak sama dengan jenis sumber daya")
        for j in range(m):
            jumlah = sum(d["allocation"][i][j] for i in range(n)) + d["available"][j]
            if jumlah != total[j]:
                raise DataError(
                    f"Sum(Allocation)+Available != Total pada {d['resources'][j]} ({jumlah} != {total[j]})")


def hitung_need(alloc, mx):
    """Need = Max - Allocation, per elemen."""
    return [[mx[i][j] - alloc[i][j] for j in range(len(mx[i]))] for i in range(len(mx))]


def safety(alloc, need, available):
    """Safety algorithm. Mengembalikan (aman, urutan, jejak)."""
    n = len(alloc)
    work = list(available)
    finish = [False] * n
    urutan, jejak = [], []
    while True:
        dipilih = None
        for i in range(n):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(len(work))):
                dipilih = i
                break
        if dipilih is None:
            break
        sebelum = list(work)
        work = [work[j] + alloc[dipilih][j] for j in range(len(work))]
        finish[dipilih] = True
        urutan.append(dipilih)
        jejak.append({"proses": dipilih, "work_sebelum": sebelum, "need": list(need[dipilih]),
                      "work_sesudah": list(work), "finish": list(finish)})
    macet = [{"proses": i, "need": list(need[i]), "work": list(work)} for i in range(n) if not finish[i]]
    return all(finish), urutan, jejak, macet


def cek_urutan(alloc, need, available, urutan):
    """Memutar ulang urutan aman secara independen: Need <= Work harus benar di tiap langkah."""
    work = list(available)
    for i in urutan:
        if not all(need[i][j] <= work[j] for j in range(len(work))):
            return False
        work = [work[j] + alloc[i][j] for j in range(len(work))]
    return True


def jalankan(d):
    validasi(d)
    nama = d["processes"]
    alloc, mx, avail = d["allocation"], d["max"], d["available"]
    need = hitung_need(alloc, mx)
    aman, urutan, jejak, macet = safety(alloc, need, avail)
    return {"nama": nama, "resources": d["resources"], "need": need, "aman": aman,
            "urutan": urutan, "jejak": jejak, "macet": macet,
            "urutan_valid": cek_urutan(alloc, need, avail, urutan) if aman else None}


def tampilkan(d, hasil, label_berkas):
    nama = hasil["nama"]
    T = lambda b: "T" if b else "F"
    print(f"Berkas   : {label_berkas}")
    print(f"Label    : {d.get('label', '(tanpa label)')}")
    print(f"Proses   : {' '.join(nama)}")
    print(f"Sumber   : {' '.join(d['resources'])}")
    print(f"Available: {d['available']}")
    print("Need = Max - Allocation")
    for i, p in enumerate(nama):
        print(f"  {p}: Max={d['max'][i]} - Alloc={d['allocation'][i]} = Need={hasil['need'][i]}")
    print("Iterasi safety algorithm (Work awal = Available, Finish awal semua F)")
    for k, s in enumerate(hasil["jejak"], 1):
        print(f"  {k}. periksa {nama[s['proses']]}: Need={s['need']} <= Work={s['work_sebelum']} -> ya"
              f" | Work baru={s['work_sesudah']} | Finish=[{', '.join(T(x) for x in s['finish'])}]")
    for s in hasil["macet"]:
        print(f"  -  {nama[s['proses']]}: Need={s['need']} tidak <= Work={s['work']} -> tidak bisa dipilih")
    if hasil["aman"]:
        print("HASIL: SAFE STATE. Urutan aman: " + " -> ".join(nama[i] for i in hasil["urutan"]))
        print(f"Verifikasi urutan (replay Need <= Work): {'valid' if hasil['urutan_valid'] else 'TIDAK valid'}")
    else:
        print("HASIL: UNSAFE STATE untuk konfigurasi ini (tidak ada urutan aman).")
        print("Catatan: unsafe state belum berarti deadlock sedang terjadi.")


def main(argv):
    if len(argv) != 2:
        print("Pemakaian: python3 banker.py <berkas.json>")
        return 2
    try:
        d = muat(argv[1])
        hasil = jalankan(d)
    except (DataError, OSError, json.JSONDecodeError) as e:
        print(f"DATA TIDAK VALID: {e}")
        return 2
    tampilkan(d, hasil, argv[1])
    return 0 if hasil["aman"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Pengujian banker.py. Jalankan: python3 -m unittest -v test_banker"""
import copy
import unittest

import banker

AMAN = {"resources": ["S", "B", "K"], "processes": ["C1", "C2", "C3"], "total": [1, 1, 2],
        "allocation": [[1, 0, 0], [0, 0, 1], [0, 0, 0]],
        "max": [[1, 1, 1], [0, 1, 2], [1, 1, 1]], "available": [0, 1, 1]}
TIDAK_AMAN = {"resources": ["S", "B", "K"], "processes": ["C1", "C2"], "total": [1, 1, 1],
              "allocation": [[1, 0, 0], [0, 1, 0]], "max": [[1, 1, 0], [1, 1, 0]], "available": [0, 0, 1]}
# Proses pertama tidak bisa jalan lebih dulu; urutan aman harus ditemukan lewat proses lain.
URUTAN_BERGANTUNG = {"resources": ["S", "B"], "processes": ["P1", "P2", "P3"],
                     "allocation": [[0, 1], [1, 0], [0, 0]],
                     "max": [[2, 2], [1, 1], [0, 1]], "available": [1, 1]}


class TesBanker(unittest.TestCase):
    def test_need_per_elemen(self):
        self.assertEqual(banker.hitung_need([[1, 0, 0], [0, 0, 1]], [[1, 1, 1], [0, 1, 2]]),
                         [[0, 1, 1], [0, 1, 1]])

    def test_safe_state(self):
        h = banker.jalankan(AMAN)
        self.assertTrue(h["aman"])
        self.assertEqual([h["nama"][i] for i in h["urutan"]], ["C1", "C2", "C3"])
        self.assertTrue(h["urutan_valid"])

    def test_unsafe_state(self):
        h = banker.jalankan(TIDAK_AMAN)
        self.assertFalse(h["aman"])
        self.assertEqual(h["urutan"], [])
        self.assertEqual(len(h["macet"]), 2)

    def test_urutan_bergantung(self):
        h = banker.jalankan(URUTAN_BERGANTUNG)
        self.assertTrue(h["aman"])
        self.assertEqual([h["nama"][i] for i in h["urutan"]], ["P2", "P1", "P3"])
        self.assertTrue(h["urutan_valid"])

    def test_work_diperbarui_benar(self):
        h = banker.jalankan(AMAN)
        self.assertEqual(h["jejak"][0]["work_sebelum"], [0, 1, 1])
        self.assertEqual(h["jejak"][0]["work_sesudah"], [1, 1, 1])
        self.assertEqual(h["jejak"][-1]["work_sesudah"], [1, 1, 2])

    def test_replay_menolak_urutan_salah(self):
        d = AMAN
        need = banker.hitung_need(d["allocation"], d["max"])
        self.assertFalse(banker.cek_urutan(d["allocation"], need, d["available"], [2, 1, 0]))

    def test_validasi_allocation_melebihi_max(self):
        d = copy.deepcopy(AMAN)
        d["allocation"][0][0] = 2
        with self.assertRaises(banker.DataError):
            banker.validasi(d)

    def test_validasi_nilai_negatif(self):
        d = copy.deepcopy(AMAN)
        d["available"][0] = -1
        with self.assertRaises(banker.DataError):
            banker.validasi(d)

    def test_validasi_dimensi(self):
        d = copy.deepcopy(AMAN)
        d["max"][1] = [0, 1]
        with self.assertRaises(banker.DataError):
            banker.validasi(d)

    def test_validasi_total_tidak_cocok(self):
        d = copy.deepcopy(AMAN)
        d["total"] = [2, 1, 2]
        with self.assertRaises(banker.DataError):
            banker.validasi(d)

    def test_data_kelas_kosong_ditolak(self):
        d = banker.muat("data/data_kelas.json")
        with self.assertRaises(banker.DataError):
            banker.validasi(d)


if __name__ == "__main__":
    unittest.main()

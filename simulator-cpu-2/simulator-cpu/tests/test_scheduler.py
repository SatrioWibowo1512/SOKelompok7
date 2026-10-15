"""Uji simulator. Nilai 'expected' adalah HASIL PERHITUNGAN MANUAL (ditulis sebelum program dijalankan)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import scheduler_sim as sim  # noqa: E402
from scheduler_sim import Process  # noqa: E402

DATA = list(sim.DATASET_KELAS)

# Gantt manual: (pid, mulai, selesai); metrik manual: (avg WT, avg TAT, avg RT, context switch)
MANUAL = {
    "FCFS": ([("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 18), ("P4", 18, 22), ("P5", 22, 28)],
             (7.4, 13.0, 7.4, 4)),
    "SJF": ([("P1", 0, 5), ("P2", 5, 8), ("P4", 8, 12), ("P5", 12, 18), ("P3", 18, 28)],
            (5.4, 11.0, 5.4, 4)),
    "SRTF": ([("P1", 0, 5), ("P2", 5, 8), ("P4", 8, 12), ("P5", 12, 18), ("P3", 18, 28)],
             (5.4, 11.0, 5.4, 4)),
    "PRIO_NP": ([("P1", 0, 5), ("P2", 5, 8), ("P4", 8, 12), ("P5", 12, 18), ("P3", 18, 28)],
                (5.4, 11.0, 5.4, 4)),
    "PRIO_P": ([("P1", 0, 2), ("P2", 2, 5), ("P1", 5, 8), ("P4", 8, 12), ("P5", 12, 18), ("P3", 18, 28)],
               (5.4, 11.0, 4.8, 5)),
    "RR4": ([("P1", 0, 4), ("P2", 4, 7), ("P3", 7, 11), ("P4", 11, 15), ("P1", 15, 16),
             ("P5", 16, 20), ("P3", 20, 24), ("P5", 24, 26), ("P3", 26, 28)],
            (9.6, 15.2, 4.4, 8)),
    "RR6": ([("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 14), ("P4", 14, 18), ("P5", 18, 24), ("P3", 24, 28)],
            (7.8, 13.4, 5.8, 5)),
    "SRTF_PREEMPT_TIE": ([("P1", 0, 2), ("P2", 2, 5), ("P1", 5, 8), ("P4", 8, 12), ("P5", 12, 18),
                          ("P3", 18, 28)], (5.4, 11.0, 4.8, 5)),
}

# CT manual per proses (urutan P1..P5)
MANUAL_CT = {
    "FCFS": [5, 8, 18, 22, 28],
    "SJF": [5, 8, 28, 12, 18],
    "PRIO_P": [8, 5, 28, 12, 18],
    "RR4": [16, 7, 28, 15, 26],
    "RR6": [5, 8, 28, 18, 24],
}


def evaluate(name, slices):
    return sim.evaluate(name, DATA, slices)


class TestDatasetKelas(unittest.TestCase):
    def check(self, key, slices):
        expected_slices, (wt, tat, rt, cs) = MANUAL[key]
        self.assertEqual(slices, expected_slices)
        result = evaluate(key, slices)
        self.assertAlmostEqual(result.avg_wt, wt)
        self.assertAlmostEqual(result.avg_tat, tat)
        self.assertAlmostEqual(result.avg_rt, rt)
        self.assertEqual(result.context_switches, cs)
        self.assertTrue(all(ok for _, ok in result.checks))
        if key in MANUAL_CT:
            self.assertEqual([r["ct"] for r in result.rows], MANUAL_CT[key])

    def test_fcfs(self):
        self.check("FCFS", sim.fcfs(DATA))

    def test_sjf(self):
        self.check("SJF", sim.sjf(DATA))

    def test_srtf(self):
        self.check("SRTF", sim.srtf(DATA))

    def test_priority_non_preemptive(self):
        self.check("PRIO_NP", sim.priority_non_preemptive(DATA))

    def test_priority_preemptive(self):
        self.check("PRIO_P", sim.priority_preemptive(DATA))

    def test_rr_q4(self):
        self.check("RR4", sim.round_robin(DATA, 4))

    def test_rr_q6(self):
        self.check("RR6", sim.round_robin(DATA, 6))

    def test_srtf_tie_preempt_sensitivity(self):
        self.check("SRTF_PREEMPT_TIE", sim.srtf(DATA, tie_policy="preempt"))

    def test_input_tidak_berubah(self):
        before = tuple(DATA)
        sim.run_all(DATA, sensitivity=True)
        self.assertEqual(tuple(DATA), before)


class TestKasusBatas(unittest.TestCase):
    def test_satu_proses(self):
        data = [Process("P1", 0, 5, 1)]
        for slices in (sim.fcfs(data), sim.sjf(data), sim.srtf(data),
                       sim.priority_non_preemptive(data), sim.priority_preemptive(data),
                       sim.round_robin(data, 2)):
            self.assertEqual(slices, [("P1", 0, 5)])
            r = sim.evaluate("x", data, slices)
            self.assertEqual((r.avg_wt, r.avg_tat, r.avg_rt, r.context_switches), (0, 5, 0, 0))

    def test_cpu_idle(self):
        data = [Process("P1", 2, 3, 1), Process("P2", 10, 2, 1)]
        expected = [(sim.IDLE, 0, 2), ("P1", 2, 5), (sim.IDLE, 5, 10), ("P2", 10, 12)]
        for slices in (sim.fcfs(data), sim.sjf(data), sim.srtf(data),
                       sim.priority_non_preemptive(data), sim.priority_preemptive(data),
                       sim.round_robin(data, 2)):
            self.assertEqual(slices, expected)
        r = sim.evaluate("x", data, sim.fcfs(data))
        self.assertEqual([x["ct"] for x in r.rows], [5, 12])
        self.assertEqual((r.avg_wt, r.avg_rt), (0, 0))
        self.assertTrue(all(ok for _, ok in r.checks))

    def test_burst_dan_prioritas_sama_arrival_sama(self):
        data = [Process("P1", 0, 4, 2), Process("P2", 0, 4, 2)]
        for slices in (sim.fcfs(data), sim.sjf(data), sim.srtf(data),
                       sim.priority_non_preemptive(data), sim.priority_preemptive(data)):
            self.assertEqual(slices, [("P1", 0, 4), ("P2", 4, 8)])
        r = sim.evaluate("x", data, sim.fcfs(data))
        self.assertEqual((r.avg_wt, r.avg_tat, r.avg_rt), (2, 6, 2))

    def test_rr_selesai_sebelum_quantum_dan_melebihi_quantum(self):
        data = [Process("P1", 0, 4, 2), Process("P2", 0, 4, 2)]
        slices = sim.round_robin(data, 2)
        self.assertEqual(slices, [("P1", 0, 2), ("P2", 2, 4), ("P1", 4, 6), ("P2", 6, 8)])
        r = sim.evaluate("x", data, slices)
        self.assertEqual([x["ct"] for x in r.rows], [6, 8])
        self.assertEqual((r.avg_wt, r.avg_tat, r.avg_rt), (3, 7, 1))

    def test_input_tidak_valid(self):
        with self.assertRaises(ValueError):
            sim.validate_processes([Process("P1", 0, 0, 1)])
        with self.assertRaises(ValueError):
            sim.validate_processes([Process("P1", 0, 1, 1), Process("P1", 1, 1, 1)])
        with self.assertRaises(ValueError):
            sim.round_robin(DATA, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

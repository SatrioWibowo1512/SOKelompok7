"""Simulator Penjadwalan CPU (Tugas K-2 Sistem Operasi, Kelas D).

Algoritma: FCFS, SJF non-preemptive, SRTF, Priority (non-preemptive dan
preemptive), Round Robin (quantum bebas). Hanya memakai pustaka standar Python 3.

Aturan yang dipakai di seluruh program (sama dengan perhitungan manual di laporan):
  * Satuan waktu bilangan bulat. Angka prioritas lebih kecil = prioritas lebih tinggi.
  * Tie-breaking: nilai kunci algoritma sama -> arrival time lebih awal -> nomor proses lebih kecil.
  * SRTF/Priority preemptive: proses yang sedang berjalan TIDAK digantikan jika nilainya
    hanya SERI dengan proses lain (tie_policy="keep"). Varian sensitivitas tie_policy="preempt"
    mengganti proses yang sedang berjalan saat seri.
  * Round Robin: proses yang tiba tepat pada saat sebuah jatah quantum berakhir masuk antrean
    SEBELUM proses yang baru saja di-preempt dikembalikan ke antrean.
  * Context switch = perpindahan CPU antara dua proses berbeda pada irisan Gantt yang
    berurutan (awal jadwal, akhir jadwal, dan perpindahan lewat IDLE tidak dihitung).
  * Overhead context switch dianggap 0 (model dasar).
"""

import argparse
import csv
import sys
from collections import deque
from dataclasses import dataclass

IDLE = "IDLE"


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int


# ---------------------------------------------------------------- data & validasi

DATASET_KELAS = (
    Process("P1", 0, 5, 2),
    Process("P2", 2, 3, 1),
    Process("P3", 3, 10, 4),
    Process("P4", 4, 4, 2),
    Process("P5", 7, 6, 3),
)


def validate_processes(processes):
    """Memeriksa dataset; melempar ValueError jika tidak valid."""
    if not processes:
        raise ValueError("Dataset kosong.")
    seen = set()
    for p in processes:
        if p.pid in seen:
            raise ValueError(f"ID proses ganda: {p.pid}")
        seen.add(p.pid)
        if p.arrival < 0:
            raise ValueError(f"{p.pid}: arrival time tidak boleh negatif.")
        if p.burst <= 0:
            raise ValueError(f"{p.pid}: burst time harus lebih dari 0.")


def load_csv(path):
    """Membaca CSV berkolom pid,arrival,burst,priority (baris pertama = header)."""
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"pid", "arrival", "burst", "priority"}
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                raise ValueError("Header CSV harus: pid,arrival,burst,priority")
            processes = []
            for number, row in enumerate(reader, start=2):
                try:
                    processes.append(Process(row["pid"].strip(), int(row["arrival"]),
                                             int(row["burst"]), int(row["priority"])))
                except (TypeError, ValueError):
                    raise ValueError(f"Baris {number}: arrival/burst/priority harus bilangan bulat.")
    except OSError as error:
        raise ValueError(f"Tidak dapat membuka berkas: {error}")
    validate_processes(processes)
    return processes


# ---------------------------------------------------------------- utilitas

def _pid_number(pid):
    digits = "".join(ch for ch in pid if ch.isdigit())
    return int(digits) if digits else 0


def _arrival_key(p):
    return (p.arrival, _pid_number(p.pid))


def _merge(slices):
    """Menggabungkan irisan berurutan milik proses yang sama."""
    merged = []
    for pid, start, end in slices:
        if merged and merged[-1][0] == pid and merged[-1][2] == start:
            merged[-1] = (pid, merged[-1][1], end)
        else:
            merged.append((pid, start, end))
    return merged


# ---------------------------------------------------------------- algoritma

def _non_preemptive(processes, key):
    pending = sorted(processes, key=_arrival_key)
    time = 0
    slices = []
    while pending:
        ready = [p for p in pending if p.arrival <= time]
        if not ready:
            next_arrival = min(p.arrival for p in pending)
            slices.append((IDLE, time, next_arrival))
            time = next_arrival
            continue
        chosen = min(ready, key=key)
        slices.append((chosen.pid, time, time + chosen.burst))
        time += chosen.burst
        pending.remove(chosen)
    return _merge(slices)


def fcfs(processes):
    return _non_preemptive(processes, key=_arrival_key)


def sjf(processes):
    """SJF non-preemptive: burst terpendek di antara proses yang sudah tiba."""
    return _non_preemptive(processes, key=lambda p: (p.burst, p.arrival, _pid_number(p.pid)))


def priority_non_preemptive(processes):
    return _non_preemptive(processes, key=lambda p: (p.priority, p.arrival, _pid_number(p.pid)))


def _preemptive(processes, primary, tie_policy):
    """Mesin per satuan waktu untuk SRTF dan Priority preemptive.

    primary(p, sisa) menghasilkan nilai yang diminimalkan (sisa burst atau prioritas).
    """
    if tie_policy not in ("keep", "preempt"):
        raise ValueError("tie_policy harus 'keep' atau 'preempt'.")
    procs = sorted(processes, key=_arrival_key)
    by_pid = {p.pid: p for p in procs}
    remaining = {p.pid: p.burst for p in procs}
    time = 0
    current = None
    finished = 0
    slices = []
    while finished < len(procs):
        ready = [p for p in procs if p.arrival <= time and remaining[p.pid] > 0]
        if not ready:
            next_arrival = min(p.arrival for p in procs if remaining[p.pid] > 0)
            slices.append((IDLE, time, next_arrival))
            time = next_arrival
            current = None
            continue
        best = min(primary(p, remaining[p.pid]) for p in ready)
        tied = sorted((p for p in ready if primary(p, remaining[p.pid]) == best),
                      key=_arrival_key)
        chosen = tied[0]
        if current is not None and remaining[current] > 0 and by_pid[current] in tied:
            if tie_policy == "keep":
                chosen = by_pid[current]
            else:
                others = [p for p in tied if p.pid != current]
                chosen = others[0] if others else by_pid[current]
        slices.append((chosen.pid, time, time + 1))
        remaining[chosen.pid] -= 1
        time += 1
        current = chosen.pid
        if remaining[chosen.pid] == 0:
            finished += 1
    return _merge(slices)


def srtf(processes, tie_policy="keep"):
    return _preemptive(processes, lambda p, rest: rest, tie_policy)


def priority_preemptive(processes, tie_policy="keep"):
    return _preemptive(processes, lambda p, rest: p.priority, tie_policy)


def round_robin(processes, quantum):
    if quantum <= 0:
        raise ValueError("Quantum harus lebih dari 0.")
    procs = sorted(processes, key=_arrival_key)
    remaining = {p.pid: p.burst for p in procs}
    queue = deque()
    next_index = 0
    time = 0
    done = 0
    slices = []
    while next_index < len(procs) and procs[next_index].arrival <= time:
        queue.append(procs[next_index])
        next_index += 1
    while done < len(procs):
        if not queue:
            next_arrival = procs[next_index].arrival
            slices.append((IDLE, time, next_arrival))
            time = next_arrival
            while next_index < len(procs) and procs[next_index].arrival <= time:
                queue.append(procs[next_index])
                next_index += 1
            continue
        p = queue.popleft()
        run = min(quantum, remaining[p.pid])
        slices.append((p.pid, time, time + run))
        time += run
        remaining[p.pid] -= run
        # kedatangan sampai (dan termasuk) saat ini masuk antrean SEBELUM proses yang di-preempt
        while next_index < len(procs) and procs[next_index].arrival <= time:
            queue.append(procs[next_index])
            next_index += 1
        if remaining[p.pid] > 0:
            queue.append(p)
        else:
            done += 1
    return _merge(slices)


# ---------------------------------------------------------------- metrik & verifikasi

def compute_metrics(processes, slices):
    """Menghitung First Start, CT, TAT, WT, RT per proses (rumus dari lembar tugas)."""
    rows = []
    for p in sorted(processes, key=lambda x: _pid_number(x.pid)):
        own = [(s, e) for pid, s, e in slices if pid == p.pid]
        if not own:
            raise ValueError(f"{p.pid} tidak pernah dijadwalkan.")
        first_start = min(s for s, _ in own)
        completion = max(e for _, e in own)
        turnaround = completion - p.arrival
        waiting = turnaround - p.burst
        response = first_start - p.arrival
        rows.append({"pid": p.pid, "arrival": p.arrival, "burst": p.burst,
                     "priority": p.priority, "first_start": first_start, "ct": completion,
                     "wt": waiting, "tat": turnaround, "rt": response})
    return rows


def count_context_switches(slices):
    count = 0
    for before, after in zip(slices, slices[1:]):
        if before[0] != IDLE and after[0] != IDLE and before[0] != after[0]:
            count += 1
    return count


def verify(processes, slices, rows):
    """Daftar (nama pemeriksaan, lulus?) sesuai bagian H.8 tugas."""
    checks = []
    busy = [(pid, s, e) for pid, s, e in slices if pid != IDLE]
    checks.append(("Total waktu CPU = total burst",
                   sum(e - s for _, s, e in busy) == sum(p.burst for p in processes)))
    arrival = {p.pid: p.arrival for p in processes}
    checks.append(("Tidak ada proses jalan sebelum arrival",
                   all(s >= arrival[pid] for pid, s, _ in busy)))
    executed = {p.pid: 0 for p in processes}
    for pid, s, e in busy:
        executed[pid] += e - s
    checks.append(("Setiap proses mendapat CPU tepat sebesar burst-nya",
                   all(executed[p.pid] == p.burst for p in processes)))
    ordered = sorted(slices, key=lambda x: x[1])
    checks.append(("Tidak ada irisan Gantt yang tumpang tindih / durasi positif",
                   all(e > s for _, s, e in ordered) and
                   all(a[2] <= b[1] for a, b in zip(ordered, ordered[1:]))))
    checks.append(("TAT = CT - AT, WT = TAT - BT, RT = FirstStart - AT konsisten",
                   all(r["tat"] == r["ct"] - r["arrival"] and r["wt"] == r["tat"] - r["burst"]
                       and r["rt"] == r["first_start"] - r["arrival"] for r in rows)))
    checks.append(("WT, RT tidak negatif dan RT <= WT",
                   all(r["wt"] >= 0 and r["rt"] >= 0 and r["rt"] <= r["wt"] for r in rows)))
    return checks


@dataclass
class Result:
    name: str
    slices: list
    rows: list
    avg_wt: float
    avg_tat: float
    avg_rt: float
    context_switches: int
    checks: list


def evaluate(name, processes, slices):
    rows = compute_metrics(processes, slices)
    n = len(rows)
    return Result(name, slices, rows,
                  sum(r["wt"] for r in rows) / n,
                  sum(r["tat"] for r in rows) / n,
                  sum(r["rt"] for r in rows) / n,
                  count_context_switches(slices),
                  verify(processes, slices, rows))


def run_all(processes, quanta=(4, 6), sensitivity=False):
    """Menjalankan semua algoritma pada data yang sama (data asli tidak diubah)."""
    validate_processes(processes)
    data = tuple(processes)
    plan = [("FCFS", fcfs(data)),
            ("SJF non-preemptive", sjf(data)),
            ("SRTF", srtf(data)),
            ("Priority non-preemptive", priority_non_preemptive(data)),
            ("Priority preemptive", priority_preemptive(data))]
    for q in quanta:
        plan.append((f"Round Robin q={q}", round_robin(data, q)))
    if sensitivity:
        plan.append(("SRTF (seri -> preempt)", srtf(data, tie_policy="preempt")))
    return [evaluate(name, data, slices) for name, slices in plan]


# ---------------------------------------------------------------- tampilan

def gantt_compact(slices):
    parts = [str(slices[0][1])]
    for pid, _, end in slices:
        parts.append(pid)
        parts.append(str(end))
    return " | ".join(parts)


def gantt_text(slices):
    bar = "|"
    axis = ""
    for pid, start, end in slices:
        width = max((end - start) * 3, len(pid) + 2)
        bar += pid.center(width) + "|"
        axis += str(start).ljust(width + 1)
    axis += str(slices[-1][2])
    return bar + "\n" + axis


def format_result(result):
    lines = [f"=== {result.name} ===",
             "Gantt : " + gantt_compact(result.slices),
             gantt_text(result.slices), "",
             f"{'Proses':<7}{'AT':>3}{'BT':>4}{'Pri':>4}{'Start':>7}{'CT':>4}{'WT':>4}{'TAT':>5}{'RT':>4}"]
    for r in result.rows:
        lines.append(f"{r['pid']:<7}{r['arrival']:>3}{r['burst']:>4}{r['priority']:>4}"
                     f"{r['first_start']:>7}{r['ct']:>4}{r['wt']:>4}{r['tat']:>5}{r['rt']:>4}")
    n = len(result.rows)
    lines.append(f"Rata-rata WT  = {sum(r['wt'] for r in result.rows)}/{n} = {result.avg_wt:.2f}")
    lines.append(f"Rata-rata TAT = {sum(r['tat'] for r in result.rows)}/{n} = {result.avg_tat:.2f}")
    lines.append(f"Rata-rata RT  = {sum(r['rt'] for r in result.rows)}/{n} = {result.avg_rt:.2f}")
    lines.append(f"Context switch = {result.context_switches}")
    for label, ok in result.checks:
        lines.append(f"  [{'OK' if ok else 'GAGAL'}] {label}")
    return "\n".join(lines)


def format_comparison(results):
    lines = [f"{'Algoritma':<38}{'Avg WT':>8}{'Avg TAT':>9}{'Avg RT':>8}{'CS':>4}"]
    for r in results:
        lines.append(f"{r.name:<38}{r.avg_wt:>8.2f}{r.avg_tat:>9.2f}{r.avg_rt:>8.2f}{r.context_switches:>4}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulator penjadwalan CPU (K-2 Sistem Operasi).")
    parser.add_argument("--dataset", help="berkas CSV pid,arrival,burst,priority (bawaan: dataset kelas P1-P5)")
    parser.add_argument("--quantum", type=int, nargs="+", default=[4, 6], help="nilai quantum Round Robin")
    parser.add_argument("--sensitivity", action="store_true", help="tampilkan varian tie-breaking 'seri -> preempt'")
    args = parser.parse_args(argv)
    try:
        processes = load_csv(args.dataset) if args.dataset else list(DATASET_KELAS)
        results = run_all(processes, tuple(args.quantum), args.sensitivity)
    except ValueError as error:
        print(f"Kesalahan input: {error}", file=sys.stderr)
        return 1
    for result in results:
        print(format_result(result))
        print()
    print("=== TABEL PERBANDINGAN ===")
    print(format_comparison(results))
    failed = [(r.name, label) for r in results for label, ok in r.checks if not ok]
    if failed:
        print("\nPEMERIKSAAN GAGAL:", failed, file=sys.stderr)
        return 2
    print("\nSemua pemeriksaan konsistensi internal lulus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
